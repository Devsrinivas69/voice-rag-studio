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
    """Gemini LLM generation service using the official google-genai SDK."""

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

    def generate_grounded_answer(
        self,
        prompt_data: Dict[str, str],
        retrieved_chunks: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generates grounded answer using Gemini API with strict system instructions."""
        system_instruction = prompt_data["system_instruction"]
        user_prompt = prompt_data["user_prompt"]

        if self.client is not None:
            try:
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

                generated_text = response.text.strip() if response.text else ""
                return {
                    "answer": generated_text,
                    "model_used": self.model_name,
                    "mock": False,
                }
            except Exception as err:
                logger.error(f"Gemini API generation error: {err}. Falling back to grounded context synthesis.")

        # Fallback grounded context synthesis for offline/mock mode
        if retrieved_chunks:
            top_passage = retrieved_chunks[0].get("text", "")
            ans = f"ಆಧಾರಿತ ಉತ್ತರ (Grounded Answer): {top_passage[:300]}"
        else:
            ans = "I cannot answer this question based on the provided context."

        return {
            "answer": ans,
            "model_used": "mock-fallback",
            "mock": True,
        }
