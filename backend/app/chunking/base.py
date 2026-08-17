from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


def create_chunk(
    document_id: str,
    text: str,
    language: str,
    strategy: str,
    position: int,
    source_query: Optional[str] = None,
    source_answer: Optional[str] = None,
    passage_index: Optional[int] = None,
    is_selected: bool = False,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Helper function to format a standardized chunk payload."""
    metadata = {
        "passage_index": passage_index if passage_index is not None else 0,
        "is_selected": is_selected,
        "length_chars": len(text),
        "length_words": len(text.split()),
    }
    if additional_metadata:
        metadata.update(additional_metadata)

    chunk_id = f"{document_id}_{strategy}_{position}"

    return {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "text": text,
        "language": language,
        "strategy": strategy,
        "position": position,
        "source_query": source_query or "",
        "source_answer": source_answer or "",
        "metadata": metadata,
    }


class BaseChunker(ABC):
    """Abstract base class for all chunking strategies."""

    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name

    @abstractmethod
    def chunk(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Splits a document dict into a list of standardized chunk dicts."""
        pass
