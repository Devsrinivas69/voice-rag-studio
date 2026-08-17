import re
from typing import Any, Dict, List, Optional
from backend.app.chunking.base import BaseChunker, create_chunk
from backend.app.config import get_settings


def split_sentences(text: str) -> List[str]:
    """Splits text into sentences using Indic and Latin sentence boundaries."""
    if not text:
        return []
    # Split on double pipe ||, danda ।, period, question mark, exclamation, or double newlines
    pattern = r"(?<=[।\.\?!])\s+|\n{2,}"
    raw = re.split(pattern, text)
    return [s.strip() for s in raw if s and s.strip()]


class SentenceChunker(BaseChunker):
    """Accumulates complete sentences up to target token limit without breaking sentence boundaries."""

    def __init__(self, target_chunk_size: Optional[int] = None):
        super().__init__(strategy_name="sentence")
        settings = get_settings()
        self.target_chunk_size = target_chunk_size or settings.CHUNK_SIZE

    def chunk(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        doc_id = document["document_id"]
        language = document.get("language", "en")
        query = document.get("query", "")
        answer = document.get("answer", "")
        passages = document.get("passages", [])

        chunks: List[Dict[str, Any]] = []
        global_pos = 0

        for p in passages:
            p_idx = p.get("passage_index", 0)
            p_text = p.get("text", "")
            is_selected = p.get("is_selected", False)

            sentences = split_sentences(p_text)
            if not sentences:
                continue

            current_sentences: List[str] = []
            current_word_count = 0

            for sent in sentences:
                sent_words = len(sent.split())

                # If single sentence exceeds target_chunk_size and current accumulator is empty
                if sent_words >= self.target_chunk_size and not current_sentences:
                    chunk_payload = create_chunk(
                        document_id=doc_id,
                        text=sent,
                        language=language,
                        strategy=self.strategy_name,
                        position=global_pos,
                        source_query=query,
                        source_answer=answer,
                        passage_index=p_idx,
                        is_selected=is_selected,
                        additional_metadata={"sentence_count": 1, "oversized_sentence": True},
                    )
                    chunks.append(chunk_payload)
                    global_pos += 1
                    continue

                # If adding sent would exceed target_chunk_size and we already have sentences
                if current_word_count + sent_words > self.target_chunk_size and current_sentences:
                    chunk_text = " ".join(current_sentences)
                    chunk_payload = create_chunk(
                        document_id=doc_id,
                        text=chunk_text,
                        language=language,
                        strategy=self.strategy_name,
                        position=global_pos,
                        source_query=query,
                        source_answer=answer,
                        passage_index=p_idx,
                        is_selected=is_selected,
                        additional_metadata={"sentence_count": len(current_sentences)},
                    )
                    chunks.append(chunk_payload)
                    global_pos += 1

                    current_sentences = [sent]
                    current_word_count = sent_words
                else:
                    current_sentences.append(sent)
                    current_word_count += sent_words

            # Emit any remaining accumulated sentences
            if current_sentences:
                chunk_text = " ".join(current_sentences)
                chunk_payload = create_chunk(
                    document_id=doc_id,
                    text=chunk_text,
                    language=language,
                    strategy=self.strategy_name,
                    position=global_pos,
                    source_query=query,
                    source_answer=answer,
                    passage_index=p_idx,
                    is_selected=is_selected,
                    additional_metadata={"sentence_count": len(current_sentences)},
                )
                chunks.append(chunk_payload)
                global_pos += 1

        return chunks
