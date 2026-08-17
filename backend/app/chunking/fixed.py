from typing import Any, Dict, List, Optional
from backend.app.chunking.base import BaseChunker, create_chunk
from backend.app.config import get_settings


class FixedTokenChunker(BaseChunker):
    """Chunks document passages into fixed token/word windows with configurable size and overlap."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        super().__init__(strategy_name="fixed")
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly smaller than chunk_size ({self.chunk_size})"
            )

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

            words = p_text.split()
            if not words:
                continue

            step = self.chunk_size - self.chunk_overlap
            for i in range(0, len(words), step):
                chunk_words = words[i : i + self.chunk_size]
                if not chunk_words:
                    continue

                chunk_text = " ".join(chunk_words)
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
                    additional_metadata={
                        "token_count": len(chunk_words),
                        "chunk_size_setting": self.chunk_size,
                        "chunk_overlap_setting": self.chunk_overlap,
                    },
                )
                chunks.append(chunk_payload)
                global_pos += 1

                # If this window reached the end of words, stop sliding for this passage
                if i + self.chunk_size >= len(words):
                    break

        return chunks
