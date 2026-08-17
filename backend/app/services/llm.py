import concurrent.futures
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class LLMService:
    """Gemini LLM generation service using the official google-genai SDK with strict timeout protection."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.LLM_MODEL
        self.api_key = settings.GEMINI_API_KEY
        self.mock_mode = settings.MOCK_EXTERNAL_APIS
        self.client: Optional[Any] = None

        self._initialize_client()

    def _initialize_client(self):
        if self.mock_mode or not self.api_key:
            logger.info("Operating Gemini LLMService in mock/fallback mode.")
            return

        if not GENAI_AVAILABLE:
            logger.warning("google-genai SDK not installed. Operating in mock mode.")
            return

        try:
            logger.info(f"Initializing google-genai client with model '{self.model_name}'...")
            self.client = genai.Client(api_key=self.api_key)
        except Exception as err:
            logger.warning(f"Could not initialize genai.Client: {err}. Operating in mock mode.")
            self.client = None

    def _call_gemini_api(self, prompt_data: Dict[str, str], temperature: float) -> str:
        """Internal helper executing Gemini API call."""
        system_instruction = prompt_data["system_instruction"]
        user_prompt = prompt_data["user_prompt"]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=1024,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=config,
        )

        return response.text.strip() if response and response.text else ""

    def generate_grounded_answer(
        self,
        prompt_data: Dict[str, str],
        retrieved_chunks: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates grounded answer using Gemini API with 5.0s maximum timeout protection."""
        if self.client is not None:
            try:
                # Wrap API call in thread pool executor with 5s hard timeout to prevent pipeline stalls
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._call_gemini_api, prompt_data, temperature)
                    generated_text = future.result(timeout=5.0)

                if generated_text:
                    return {
                        "answer": generated_text,
                        "model_used": self.model_name,
                        "mock": False,
                    }
            except concurrent.futures.TimeoutError:
                logger.warning("Gemini API call timed out (> 5.0s). Using grounded context synthesis fallback.")
            except Exception as err:
                logger.error(f"Gemini API generation error: {err}. Falling back to grounded context synthesis.")

        # Fallback grounded context synthesis for offline/mock/timeout mode
        if retrieved_chunks:
            top_passage = retrieved_chunks[0].get("text", "")
            ans = f"Grounding evidence answer: {top_passage[:350]}"
        else:
            ans = "I cannot answer this question based on the provided context."

        return {
            "answer": ans,
            "model_used": "grounded-fallback",
            "mock": True,
        }
