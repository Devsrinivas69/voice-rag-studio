from typing import List, Optional
import numpy as np
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingService:
    """Local multilingual embedding service using sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        if self._model is None:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("sentence-transformers not installed. Using 1024-dim fallback vectorizer.")
                self._model = "fallback"
                self._dimension = 1024
                return

            logger.info(f"Loading local embedding model '{self.model_name}'...")
            try:
                self._model = SentenceTransformer(self.model_name)
                # Compute test dimension
                test_emb = self._model.encode(["test"], normalize_embeddings=True)
                self._dimension = test_emb.shape[1]
                logger.info(f"Embedding model loaded successfully. Dimension: {self._dimension}")
            except Exception as err:
                logger.warning(
                    f"Could not load SentenceTransformer('{self.model_name}'): {err}. "
                    f"Using 1024-dim fallback vectorizer for local dev."
                )
                self._model = "fallback"
                self._dimension = 1024

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension or 1024

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates L2-normalized float embeddings for a list of input texts."""
        if not texts:
            return []

        self._load_model()

        if self._model != "fallback":
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return embeddings.tolist()
        else:
            # Deterministic pseudo-embedding for fallback/mock mode
            results = []
            for t in texts:
                # Seed RNG with text hash for deterministic vector
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
