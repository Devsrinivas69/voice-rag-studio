from typing import Any, Dict, List
from backend.app.chunking.base import BaseChunker, create_chunk


class MetadataAwareChunker(BaseChunker):
    """Generates structure-aware chunks preserving rich passage metadata, selection status, and source query context."""

    def __init__(self):
        super().__init__(strategy_name="metadata_aware")

    def chunk(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        doc_id = document["document_id"]
        language = document.get("language", "en")
        query = document.get("query", "")
        eng_query = document.get("english_query", "")
        answer = document.get("answer", "")
        eng_answer = document.get("english_answer", "")
        passages = document.get("passages", [])

        chunks: List[Dict[str, Any]] = []

        for pos, p in enumerate(passages):
            p_idx = p.get("passage_index", pos)
            p_text = p.get("text", "")
            is_selected = p.get("is_selected", False)
            eng_text = p.get("english_text", "")

            if not p_text:
                continue

            chunk_payload = create_chunk(
                document_id=doc_id,
                text=p_text,
                language=language,
                strategy=self.strategy_name,
                position=pos,
                source_query=query,
                source_answer=answer,
                passage_index=p_idx,
                is_selected=is_selected,
                additional_metadata={
                    "english_query": eng_query,
                    "english_answer": eng_answer,
                    "english_passage_text": eng_text,
                    "query_id": document.get("query_id"),
                    "total_passages_in_doc": len(passages),
                },
            )
            chunks.append(chunk_payload)

        return chunks
