from typing import List, Optional, Tuple
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False


class RerankerService:
    """Local Cross-Encoder reranker service for scoring (query, passage) pairs."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.RERANKER_MODEL
        self._model = None

    def _load_model(self):
        if self._model is None:
            if not CROSS_ENCODER_AVAILABLE:
                logger.warning("sentence-transformers not installed. Using fallback reranker.")
                self._model = "fallback"
                return

            logger.info(f"Loading local Cross-Encoder model '{self.model_name}'...")
            try:
                self._model = CrossEncoder(self.model_name)
                logger.info(f"Reranker model '{self.model_name}' loaded successfully.")
            except Exception as err:
                logger.warning(
                    f"Could not load CrossEncoder('{self.model_name}'): {err}. "
                    f"Using term-overlap fallback reranker for local dev."
                )
                self._model = "fallback"

    def predict_scores(self, query: str, texts: List[str]) -> List[float]:
        """Scores candidate texts against query. Returns relevance scores float list."""
        if not texts or not query:
            return [0.0] * len(texts)

        self._load_model()

        if self._model != "fallback":
            try:
                pairs: List[Tuple[str, str]] = [(query, t) for t in texts]
                scores = self._model.predict(pairs)
                if hasattr(scores, "tolist"):
                    return scores.tolist()
                return list(scores)
            except Exception as err:
                logger.error(f"Reranker predict error: {err}. Falling back to basic score.")
                return [0.0] * len(texts)
        else:
            # Fallback simple keyword overlap ratio score
            query_words = set(query.lower().split())
            scores = []
            for t in texts:
                t_words = set(t.lower().split())
                overlap = len(query_words.intersection(t_words))
                scores.append(float(overlap) / float(len(query_words) or 1))
            return scores
