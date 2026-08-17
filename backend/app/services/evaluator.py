import re
from typing import Any, Dict, List
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

REFUSAL_PHRASES = [
    "i cannot answer this question",
    "cannot answer based on the provided context",
    "provided context does not contain",
    "not enough information",
    "ಉತ್ತರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ",
]


class GroundingEvaluator:
    """Evaluates answer groundedness against retrieved context and detects low-relevance refusal scenarios."""

    def __init__(self, min_relevance_threshold: float = 0.010):
        settings = get_settings()
        self.min_relevance_threshold = min_relevance_threshold or settings.GROUNDING_THRESHOLD

    def is_refusal_answer(self, answer: str) -> bool:
        """Checks if generated answer is an explicit refusal."""
        if not answer:
            return True
        ans_lower = answer.lower()
        return any(phrase in ans_lower for phrase in REFUSAL_PHRASES)

    def verify_grounding(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluates objective groundedness of generated answer against retrieved text passages."""
        if not answer or self.is_refusal_answer(answer):
            return {
                "grounded": True,
                "status": "refusal",
                "grounding_score": 1.0,
                "should_answer": False,
                "confidence": 0.0,
            }

        if not retrieved_chunks:
            return {
                "grounded": False,
                "status": "ungrounded",
                "grounding_score": 0.0,
                "should_answer": False,
                "confidence": 0.0,
            }

        # Combine all retrieved passage texts
        combined_context = " ".join([c.get("text", "") for c in retrieved_chunks]).lower()
        context_words = set(re.findall(r"\w+", combined_context))

        if not context_words:
            return {
                "grounded": False,
                "status": "ungrounded",
                "grounding_score": 0.0,
                "should_answer": False,
                "confidence": 0.0,
            }

        # Tokenize answer
        answer_words = re.findall(r"\w+", answer.lower())
        if not answer_words:
            return {
                "grounded": False,
                "status": "ungrounded",
                "grounding_score": 0.0,
                "should_answer": False,
                "confidence": 0.0,
            }

        # Calculate word overlap ratio
        overlap_count = sum(1 for w in answer_words if w in context_words)
        overlap_ratio = round(float(overlap_count) / float(len(answer_words)), 4)

        if overlap_ratio >= 0.65:
            status = "fully_grounded"
            grounded = True
            confidence = min(0.95, round(0.70 + 0.30 * overlap_ratio, 2))
        elif overlap_ratio >= 0.30:
            status = "partially_grounded"
            grounded = True
            confidence = min(0.85, round(0.50 + 0.30 * overlap_ratio, 2))
        else:
            status = "ungrounded"
            grounded = False
            confidence = max(0.10, round(overlap_ratio, 2))

        return {
            "grounded": grounded,
            "status": status,
            "grounding_score": overlap_ratio,
            "should_answer": True,
            "confidence": confidence,
        }
