import time
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger
from backend.app.monitoring.timer import LatencyTimer
from backend.app.services.bm25 import BM25Service
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.qdrant import QdrantService
from backend.app.services.reranker import RerankerService


def compute_rrf_score(dense_rank: Optional[int], sparse_rank: Optional[int], k: int = 60) -> float:
    """Computes Reciprocal Rank Fusion (RRF) score for a candidate document."""
    rrf_score = 0.0
    if dense_rank is not None and dense_rank > 0:
        rrf_score += 1.0 / (k + dense_rank)
    if sparse_rank is not None and sparse_rank > 0:
        rrf_score += 1.0 / (k + sparse_rank)
    return round(rrf_score, 6)


class HybridRetriever:
    """Hybrid Retrieval engine combining Qdrant dense vector search, BM25 sparse search, and RRF fusion."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_service: Optional[QdrantService] = None,
        bm25_service: Optional[BM25Service] = None,
        reranker_service: Optional[RerankerService] = None,
        rrf_k: Optional[int] = None,
    ):
        settings = get_settings()
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()
        self.bm25_service = bm25_service or BM25Service()
        self.reranker_service = reranker_service or RerankerService()
        self.rrf_k = rrf_k or settings.RRF_K

    def retrieve(
        self,
        query: str,
        language: Optional[str] = None,
        top_k: Optional[int] = None,
        enable_rerank: bool = False,
    ) -> Dict[str, Any]:
        """Executes dense + sparse search, computes RRF fusion, applies optional reranking, and tracks latencies."""
        settings = get_settings()
        limit = top_k or settings.TOP_K_RETRIEVAL
        raw_lang = (language or settings.DATASET_LANGUAGE or "").lower()
        # Normalize e.g. "en-in" -> "en", "kn-in" -> "kn"
        target_lang = raw_lang.split("-")[0].split("_")[0] if raw_lang else None
        if target_lang in ("all", "auto", ""):
            target_lang = None

        retrieval_timer = LatencyTimer("total_retrieval_ms")
        retrieval_timer.start()

        # 1. Dense Vector Search (Qdrant)
        with LatencyTimer("dense_search_ms") as dense_timer:
            query_vector = self.embedding_service.encode_single(query)
            dense_results = self.qdrant_service.search(
                collection_name=self.qdrant_service.collection_name,
                query_vector=query_vector,
                limit=limit * 2,
                language_filter=target_lang,
            )

        # 2. Sparse Lexical Search (BM25)
        with LatencyTimer("sparse_search_ms") as sparse_timer:
            sparse_results = self.bm25_service.search(
                query=query,
                limit=limit * 2,
                language_filter=target_lang,
            )

        # 3. Reciprocal Rank Fusion (RRF)
        with LatencyTimer("rrf_fusion_ms") as rrf_timer:
            candidate_map: Dict[str, Dict[str, Any]] = {}

            # Map dense ranks
            for rank_idx, hit in enumerate(dense_results, start=1):
                payload = hit["payload"]
                chunk_id = payload["chunk_id"]
                candidate_map[chunk_id] = {
                    "payload": payload,
                    "dense_rank": rank_idx,
                    "sparse_rank": None,
                    "dense_score": hit.get("score", 0.0),
                    "sparse_score": 0.0,
                }

            # Map sparse ranks
            for rank_idx, hit in enumerate(sparse_results, start=1):
                payload = hit["payload"]
                chunk_id = payload["chunk_id"]
                if chunk_id in candidate_map:
                    candidate_map[chunk_id]["sparse_rank"] = rank_idx
                    candidate_map[chunk_id]["sparse_score"] = hit.get("score", 0.0)
                else:
                    candidate_map[chunk_id] = {
                        "payload": payload,
                        "dense_rank": None,
                        "sparse_rank": rank_idx,
                        "dense_score": 0.0,
                        "sparse_score": hit.get("score", 0.0),
                    }

            # Compute RRF score for all candidates
            fused_candidates: List[Dict[str, Any]] = []
            for chunk_id, data in candidate_map.items():
                d_rank = data["dense_rank"]
                s_rank = data["sparse_rank"]
                rrf_score = compute_rrf_score(d_rank, s_rank, k=self.rrf_k)

                p = data["payload"]
                fused_candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": p.get("document_id", ""),
                        "text": p.get("text", ""),
                        "language": p.get("language", target_lang),
                        "strategy": p.get("strategy", "unknown"),
                        "dense_rank": d_rank,
                        "sparse_rank": s_rank,
                        "rrf_score": rrf_score,
                        "final_score": rrf_score,
                        "source_query": p.get("source_query", ""),
                        "source_answer": p.get("source_answer", ""),
                        "metadata": p.get("metadata", {}),
                    }
                )

            # Sort candidates by RRF score descending
            fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

        # 4. Optional Cross-Encoder Reranking
        rerank_timer_ms = 0.0
        if enable_rerank and fused_candidates:
            with LatencyTimer("rerank_ms") as rerank_timer:
                top_to_rerank = fused_candidates[:limit]
                texts = [c["text"] for c in top_to_rerank]
                rerank_scores = self.reranker_service.predict_scores(query, texts)

                for idx, score in enumerate(rerank_scores):
                    top_to_rerank[idx]["rerank_score"] = round(score, 6)
                    # Blend RRF score and Cross-Encoder score
                    top_to_rerank[idx]["final_score"] = round(0.5 * top_to_rerank[idx]["rrf_score"] + 0.5 * score, 6)

                top_to_rerank.sort(key=lambda x: x["final_score"], reverse=True)
                fused_candidates[:limit] = top_to_rerank

            rerank_timer_ms = rerank_timer.elapsed_ms

        retrieval_timer.stop()
        final_candidates = fused_candidates[:limit]

        latency_breakdown = {
            "dense_search_ms": dense_timer.elapsed_ms,
            "sparse_search_ms": sparse_timer.elapsed_ms,
            "rrf_fusion_ms": rrf_timer.elapsed_ms,
            "rerank_ms": rerank_timer_ms,
            "total_retrieval_ms": retrieval_timer.elapsed_ms,
        }

        logger.info(
            f"Hybrid retrieval complete for query '{query[:30]}...' "
            f"[candidates={len(final_candidates)}, total_ms={retrieval_timer.elapsed_ms}]"
        )

        return {
            "query": query,
            "language": target_lang,
            "candidates": final_candidates,
            "latency_breakdown": latency_breakdown,
        }
