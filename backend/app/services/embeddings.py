import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import numpy as np
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class EmbeddingService:
    """Multilingual embedding service using Gemini Embedding 2 API (768-dim) or fallback."""

    GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-2"
    GEMINI_EMBEDDING_DIM = 768

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dimension: Optional[int] = None
        self._gemini_client = None
        self._use_gemini_api = False

    def _load_model(self):
        if self._model is not None or self._use_gemini_api:
            return

        settings = get_settings()
        disable_local = os.getenv("DISABLE_LOCAL_TRANSFORMERS", "false").lower() == "true"

        # Strategy 1: Prefer Gemini API (zero RAM, fast cloud execution)
        if disable_local or not SENTENCE_TRANSFORMERS_AVAILABLE:
            if GENAI_AVAILABLE and settings.GEMINI_API_KEY:
                try:
                    self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    test_res = self._gemini_client.models.embed_content(
                        model=self.GEMINI_EMBEDDING_MODEL,
                        contents="test",
                        config=types.EmbedContentConfig(output_dimensionality=self.GEMINI_EMBEDDING_DIM),
                    )
                    self._dimension = len(test_res.embeddings[0].values)
                    self._use_gemini_api = True
                    logger.info(
                        f"Using Gemini Embedding API ({self.GEMINI_EMBEDDING_MODEL}, dim={self._dimension})"
                    )
                    return
                except Exception as err:
                    logger.warning(f"Gemini API init failed: {err}. Using deterministic fallback.")

            logger.warning("Using deterministic 768-dim fallback embeddings.")
            self._model = "fallback"
            self._dimension = self.GEMINI_EMBEDDING_DIM
            return

        # Strategy 2: Local SentenceTransformer
        try:
            os.environ["OMP_NUM_THREADS"] = "1"
            os.environ["MKL_NUM_THREADS"] = "1"
            self._model = SentenceTransformer(self.model_name)
            test_emb = self._model.encode(["test"], normalize_embeddings=True)
            self._dimension = test_emb.shape[1]
        except Exception as err:
            logger.warning(f"SentenceTransformer load failed: {err}. Falling back to Gemini API.")
            if GENAI_AVAILABLE and settings.GEMINI_API_KEY:
                try:
                    self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    self._use_gemini_api = True
                    self._dimension = self.GEMINI_EMBEDDING_DIM
                    return
                except Exception:
                    pass
            self._model = "fallback"
            self._dimension = self.GEMINI_EMBEDDING_DIM

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension or self.GEMINI_EMBEDDING_DIM

    def _embed_one_gemini(self, text: str) -> List[float]:
        """Embeds single string via Gemini API."""
        try:
            res = self._gemini_client.models.embed_content(
                model=self.GEMINI_EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=self.GEMINI_EMBEDDING_DIM),
            )
            return res.embeddings[0].values
        except Exception as e:
            logger.warning(f"Gemini embed error for text: {e}")
            return self._embed_deterministic_fallback([text])[0]

    def _embed_deterministic_fallback(self, texts: List[str]) -> List[List[float]]:
        results = []
        for t in texts:
            seed = abs(hash(t)) % (2**32)
            rng = np.random.RandomState(seed)
            vec = rng.randn(self.GEMINI_EMBEDDING_DIM).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []

        self._load_model()

        # Priority 1: Gemini API
        if self._use_gemini_api and self._gemini_client is not None:
            if len(texts) == 1:
                return [self._embed_one_gemini(texts[0])]
            with ThreadPoolExecutor(max_workers=min(len(texts), 8)) as executor:
                return list(executor.map(self._embed_one_gemini, texts))

        # Priority 2: SentenceTransformer
        if self._model is not None and self._model != "fallback":
            try:
                emb = self._model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
                return emb.tolist()
            except Exception:
                pass

        return self._embed_deterministic_fallback(texts)

    def encode_single(self, text: str) -> List[float]:
        res = self.encode_texts([text])
        return res[0] if res else [0.0] * self.dimension
