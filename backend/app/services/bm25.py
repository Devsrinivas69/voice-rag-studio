import os
import pickle
import re
from typing import Any, Dict, List, Optional
from backend.app.monitoring.metrics import logger

try:
    from rank_bm25 import BM25Plus, BM25Okapi
    RANK_BM25_AVAILABLE = True
except ImportError:
    RANK_BM25_AVAILABLE = False


def tokenize_bm25(text: str) -> List[str]:
    """Tokenizes Indic & English text into terms for BM25 indexing."""
    if not text:
        return []
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return [w for w in cleaned.split() if w]


class BM25Service:
    """Local open-source BM25 lexical retrieval service with index persistence and startup loading."""

    def __init__(self, index_path: str = "indices/bm25_index.pkl"):
        self.index_path = index_path
        # Also check alternative location for Docker deployments
        self._alt_paths = [
            "indices/bm25_index.pkl",
            "backend/indices/bm25_index.pkl",
        ]
        self.bm25: Optional[Any] = None
        self.chunks: List[Dict[str, Any]] = []

    def build_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """Tokenizes chunks, builds BM25Plus index, and persists index to disk."""
        if not chunks:
            logger.warning("No chunks provided to build BM25 index.")
            return False

        if not RANK_BM25_AVAILABLE:
            logger.warning("rank-bm25 package not installed. Storing raw chunks for fallback search.")
            self.chunks = chunks
            self.save_index()
            return True

        logger.info(f"Building BM25 index over {len(chunks)} chunks...")
        corpus_tokens = [tokenize_bm25(c["text"]) for c in chunks]

        try:
            self.bm25 = BM25Plus(corpus_tokens)
        except Exception:
            self.bm25 = BM25Okapi(corpus_tokens)

        self.chunks = chunks
        return self.save_index()

    def save_index(self) -> bool:
        """Persists BM25 index and chunk list to pickle file."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            with open(self.index_path, "wb") as f:
                pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
            logger.info(f"BM25 index saved to '{self.index_path}'.")
            return True
        except Exception as err:
            logger.error(f"Failed to save BM25 index to '{self.index_path}': {err}")
            return False

    def load_index(self) -> bool:
        """Loads persisted BM25 index from pickle file at application startup."""
        # Check primary path first, then alternative paths
        paths_to_check = [self.index_path] + [p for p in self._alt_paths if p != self.index_path]
        found_path = None
        for path in paths_to_check:
            if os.path.exists(path):
                found_path = path
                break

        if found_path is None:
            logger.warning(f"BM25 index file not found at any of: {paths_to_check}")
            return False

        try:
            with open(found_path, "rb") as f:
                data = pickle.load(f)
            self.bm25 = data.get("bm25")
            self.chunks = data.get("chunks", [])
            logger.info(f"Successfully loaded BM25 index from '{found_path}' with {len(self.chunks)} chunks.")
            return True
        except Exception as err:
            logger.error(f"Failed to load BM25 index from '{found_path}': {err}")
            return False

    def search(self, query: str, limit: int = 20, language_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs BM25 search and returns top-K candidates with BM25 scores."""
        if not self.chunks:
            self.load_index()

        if not self.chunks:
            return []

        query_tokens = tokenize_bm25(query)
        if not query_tokens:
            return []

        if self.bm25 is not None:
            scores = self.bm25.get_scores(query_tokens)
            results = []
            for idx, score in enumerate(scores):
                c = self.chunks[idx]
                c_lang = c.get("language", "").lower()
                if language_filter:
                    target_sub = language_filter.lower().split("-")[0].split("_")[0]
                    if not (c_lang.startswith(target_sub) or target_sub in c_lang or c_lang.startswith("kan")):
                        continue

                # Check keyword overlap for non-zero match check
                text_tokens = set(tokenize_bm25(c["text"]))
                has_match = any(qt in text_tokens for qt in query_tokens)

                if has_match or score > 0:
                    effective_score = float(score) if score > 0 else float(sum(1 for qt in query_tokens if qt in text_tokens))
                    results.append(
                        {
                            "chunk_id": c["chunk_id"],
                            "score": effective_score,
                            "payload": c,
                        }
                    )

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
        else:
            # Fallback keyword match search
            results = []
            for c in self.chunks:
                text_lower = c["text"].lower()
                matches = sum(1 for t in query_tokens if t in text_lower)
                if matches > 0:
                    results.append({"chunk_id": c["chunk_id"], "score": float(matches), "payload": c})
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
