import hashlib
from typing import Any, Dict, List, Optional, Set


class DocumentDeduplicator:
    """Hash-based deduplication for query texts, document IDs, and passage texts."""

    def __init__(self):
        self.seen_doc_ids: Set[str] = set()
        self.seen_query_hashes: Set[str] = set()
        self.seen_passage_hashes: Set[str] = set()
        self.duplicate_doc_count: int = 0
        self.duplicate_passage_count: int = 0

    @staticmethod
    def hash_text(text: str) -> str:
        """Computes SHA-256 hash of normalized text."""
        return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

    def process_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Deduplicates document and individual passages."""
        doc_id = record["document_id"]
        query_text = record["query"]

        # 1. Document ID deduplication
        if doc_id in self.seen_doc_ids:
            self.duplicate_doc_count += 1
            return None

        # 2. Query hash deduplication
        query_hash = self.hash_text(query_text)
        if query_hash in self.seen_query_hashes:
            self.duplicate_doc_count += 1
            return None

        # Mark document & query seen
        self.seen_doc_ids.add(doc_id)
        self.seen_query_hashes.add(query_hash)

        # 3. Deduplicate individual passages within the document
        deduped_passages: List[Dict[str, Any]] = []
        for passage in record.get("passages", []):
            p_hash = self.hash_text(passage["text"])
            if p_hash in self.seen_passage_hashes:
                self.duplicate_passage_count += 1
                continue

            self.seen_passage_hashes.add(p_hash)
            deduped_passages.append(passage)

        if not deduped_passages:
            return None

        record["passages"] = deduped_passages
        return record
