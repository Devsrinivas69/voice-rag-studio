import re
from typing import Any, Dict, List, Optional


def normalize_text(text: Optional[str]) -> str:
    """Strips control characters, normalizes whitespace, and trims string."""
    if not text:
        return ""
    # 1. Remove null characters or invisible control codes
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 2. Replace whitespace sequences with a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class DocumentCleaner:
    """Normalizes raw MSMARCO-XI dataset items into standardized documents."""

    def __init__(self, target_language: str = "kn"):
        self.target_language = target_language.lower()

    def clean_record(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cleans and validates a single raw item from MSMARCO-XI."""
        query_id = item.get("query_id")
        if query_id is None:
            return None

        # Determine target language query & answer
        query = normalize_text(item.get("query"))
        eng_query = normalize_text(item.get("Eng_Query"))
        effective_query = query if (query and self.target_language != "en") else (eng_query or query)

        if not effective_query:
            return None

        answer = normalize_text(item.get("Answer"))
        eng_answer = normalize_text(item.get("Eng_Answer"))
        effective_answer = answer if (answer and self.target_language != "en") else (eng_answer or answer)

        # Extract passages
        passages_obj = item.get("passages") or {}
        translated_passages = passages_obj.get("Translated_passages") or []
        english_passages = passages_obj.get("English_passages") or []
        is_selected = passages_obj.get("is_selected") or []

        # Select target passages
        passages_to_use = (
            translated_passages
            if (translated_passages and self.target_language != "en")
            else (english_passages or translated_passages)
        )

        cleaned_passages: List[Dict[str, Any]] = []
        for idx, p_text in enumerate(passages_to_use):
            norm_p = normalize_text(p_text)
            if not norm_p:
                continue

            selected_flag = bool(is_selected[idx]) if idx < len(is_selected) else False
            eng_p = (
                normalize_text(english_passages[idx])
                if idx < len(english_passages)
                else ""
            )

            cleaned_passages.append(
                {
                    "passage_index": idx,
                    "text": norm_p,
                    "english_text": eng_p,
                    "is_selected": selected_flag,
                }
            )

        if not cleaned_passages:
            return None

        raw_lang = item.get("target_lang") or self.target_language
        clean_lang = raw_lang.lower().split("_")[0].split("-")[0]
        lang_map = {"kan": "kn", "hin": "hi", "tam": "ta", "tel": "te", "mal": "ml", "mar": "mr", "ben": "bn", "guj": "gu"}
        normalized_lang = lang_map.get(clean_lang, clean_lang)

        return {
            "document_id": f"msmarco_xi_{query_id}",
            "query_id": int(query_id),
            "language": normalized_lang,
            "query": effective_query,
            "english_query": eng_query,
            "answer": effective_answer,
            "english_answer": eng_answer,
            "passages": cleaned_passages,
        }
