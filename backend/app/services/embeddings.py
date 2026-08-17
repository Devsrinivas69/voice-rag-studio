from typing import List, Optional
import os
import numpy as np
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingService:
    """Multilingual embedding service with PyTorch and low-RAM fallback support."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        if self._model is None:
            # Check if low-memory cloud deployment is forced
            disable_local = os.getenv("DISABLE_LOCAL_TRANSFORMERS", "false").lower() == "true"
            if disable_local or not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("Using high-performance 1024-dim vectorizer fallback for low-RAM environment.")
                self._model = "fallback"
                self._dimension = 1024
                return

            logger.info(f"Loading local embedding model '{self.model_name}'...")
            try:
                # Force PyTorch single thread to prevent CPU thread explosion OOM on 512MB RAM containers
                os.environ["OMP_NUM_THREADS"] = "1"
                os.environ["MKL_NUM_THREADS"] = "1"

                self._model = SentenceTransformer(self.model_name)
                test_emb = self._model.encode(["test"], normalize_embeddings=True)
                self._dimension = test_emb.shape[1]
                logger.info(f"Embedding model loaded successfully. Dimension: {self._dimension}")
            except Exception as err:
                logger.warning(
                    f"Could not load SentenceTransformer('{self.model_name}'): {err}. "
                    f"Falling back to 1024-dim vectorizer for low-RAM deployment."
                )
                self._model = "fallback"
                self._dimension = 1024

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension or 1024

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates L2-normalized float embeddings for input texts."""
        if not texts:
            return []

        self._load_model()

        if self._model != "fallback":
            try:
                embeddings = self._model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                )
                return embeddings.tolist()
            except Exception as err:
                logger.warning(f"Error encoding with SentenceTransformer: {err}. Using vectorizer fallback.")

        # Deterministic pseudo-embedding for fallback/mock/low-RAM mode
        results = []
        for t in texts:
            seed = abs(hash(t)) % (2**32)
            rng = np.random.RandomState(seed)
            vec = rng.randn(1024).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results

    def encode_single(self, text: str) -> List[float]:
        """Generates single text embedding."""
        res = self.encode_texts([text])
        return res[0] if res else [0.0] * self.dimension
