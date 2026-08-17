import re
from typing import Any, Dict, List, Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+override",
    r"you\s+are\s+now\s+a",
    r"forget\s+all\s+rules",
    r"do\s+anything\s+now",
    r"jailbreak",
]


def sanitize_user_query(query: str) -> Tuple[str, bool]:
    """Sanitizes user query against prompt injection attacks. Returns (clean_query, is_injection_flag)."""
    if not query:
        return "", False

    cleaned = query.strip()
    is_injection = False

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            is_injection = True
            cleaned = re.sub(pattern, "[removed instruction]", cleaned, flags=re.IGNORECASE)

    # Escape raw XML tags user might inject
    cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")

    return cleaned, is_injection


def build_grounded_prompt(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    language: str = "en",
) -> Dict[str, str]:
    """Formats system prompt and user prompt with structural XML boundaries for strict grounding."""
    clean_query, is_injection = sanitize_user_query(query)

    passages_xml = []
    for idx, c in enumerate(retrieved_chunks, start=1):
        p_text = c.get("text", "").strip()
        doc_id = c.get("document_id", f"doc_{idx}")
        passages_xml.append(f'<passage id="{doc_id}">\n{p_text}\n</passage>')

    context_str = "\n".join(passages_xml) if passages_xml else "<passage id='none'>No relevant context retrieved.</passage>"

    system_instruction = (
        "You are an expert, highly accurate RAG assistant for the HHGOA system. "
        "Your duty is to answer the user's question accurately using ONLY the provided retrieved context. "
        "CRITICAL RULES:\n"
        "1. Strictly base your answer ONLY on facts mentioned within the <retrieved_context> tags.\n"
        "2. Do NOT invent, assume, or bring in outside knowledge not present in the context.\n"
        "3. If the retrieved context does NOT contain sufficient information to answer the question, "
        "you MUST state clearly: 'I cannot answer this question based on the provided context.'\n"
        f"4. Respond in the user's language: '{language}'."
    )

    user_prompt = (
        f"Retrieved Context:\n"
        f"<retrieved_context>\n"
        f"{context_str}\n"
        f"</retrieved_context>\n\n"
        f"User Question: {clean_query}\n\n"
        f"Answer:"
    )

    return {
        "system_instruction": system_instruction,
        "user_prompt": user_prompt,
        "is_injection_detected": is_injection,
    }
