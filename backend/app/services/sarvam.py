import time
from typing import Any, Dict, Optional
import httpx
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

# Language code mapping helper
LANG_CODE_MAP = {
    "kn": "kn-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "as": "as-IN",
    "or": "or-IN",
    "pa": "pa-IN",
    "en": "en-IN",
}


class SarvamSTTService:
    """Sarvam AI Saaras v3 Speech-to-Text service with multi-Indic language support."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.mock_mode = settings.MOCK_EXTERNAL_APIS
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def normalize_language_code(self, lang: str) -> str:
        """Normalizes language code to Sarvam BCP-47 format (e.g. kn -> kn-IN)."""
        if not lang:
            return "kn-IN"
        clean = lang.lower().split("-")[0]
        return LANG_CODE_MAP.get(clean, f"{clean}-IN")

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: str = "kn-IN",
    ) -> Dict[str, Any]:
        """Transcribes input audio bytes using Sarvam Saaras v3 STT API."""
        start_time = time.perf_counter()
        target_lang = self.normalize_language_code(language)

        if self.mock_mode or not self.api_key:
            logger.info("Operating Sarvam STT in fallback mock mode.")
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return {
                "transcript": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು ಮತ್ತು ಅದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ?",
                "language": target_lang,
                "stt_ms": elapsed_ms,
                "mock": True,
            }

        headers = {
            "api-subscription-key": self.api_key,
        }

        files = {
            "file": (filename, audio_bytes, "audio/wav"),
        }

        data = {
            "model": "saaras:v3",
            "language_code": target_lang,
            "with_timestamps": "false",
        }

        try:
            logger.info(f"Sending STT request to Sarvam AI [file={filename}, lang={target_lang}]...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    SARVAM_STT_URL,
                    headers=headers,
                    files=files,
                    data=data,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if response.status_code == 200:
                res_data = response.json()
                transcript = res_data.get("transcript", "").strip()
                logger.info(f"Sarvam STT success in {elapsed_ms} ms: '{transcript[:40]}...'")
                return {
                    "transcript": transcript,
                    "language": target_lang,
                    "stt_ms": elapsed_ms,
                    "mock": False,
                }
            else:
                logger.error(f"Sarvam STT API error {response.status_code}: {response.text}")
        except Exception as err:
            logger.error(f"Sarvam STT connection exception: {err}. Falling back to mock transcription.")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return {
            "transcript": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?",
            "language": target_lang,
            "stt_ms": elapsed_ms,
            "mock": True,
        }
