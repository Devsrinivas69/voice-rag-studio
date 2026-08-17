from fastapi import APIRouter, Depends
from backend.app.config import Settings
from backend.app.dependencies import get_app_settings, get_request_id
from backend.app.monitoring.timer import LatencyTimer
from backend.app.schemas.query import TextQueryRequest
from backend.app.schemas.response import LatencyBreakdown, RagResponse, SourceItem
from backend.app.services.evaluator import GroundingEvaluator
from backend.app.services.llm import LLMService
from backend.app.services.prompts import build_grounded_prompt
from backend.app.services.retrieval import HybridRetriever

router = APIRouter(prefix="/api", tags=["Query"])

# Singletons
_retriever = None
_llm_service = None
_evaluator = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_evaluator() -> GroundingEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = GroundingEvaluator()
    return _evaluator


@router.post("/query", response_model=RagResponse)
async def text_query(
    body: TextQueryRequest,
    settings: Settings = Depends(get_app_settings),
    request_id: str = Depends(get_request_id),
    retriever: HybridRetriever = Depends(get_retriever),
    llm_service: LLMService = Depends(get_llm_service),
    evaluator: GroundingEvaluator = Depends(get_evaluator),
) -> RagResponse:
    """POST /api/query — End-to-end text RAG endpoint with hybrid retrieval, Gemini generation, and grounding verification."""
    latency_dict = {}

    with LatencyTimer("total_backend_ms", latency_dict):
        with LatencyTimer("query_normalization_ms", latency_dict):
            normalized_query = body.query.strip()

        with LatencyTimer("routing_ms", latency_dict):
            route = "DATASET"

        # 1. Hybrid Retrieval Stage
        retrieval_res = retriever.retrieve(
            query=normalized_query,
            language=body.language,
            top_k=body.top_k,
            enable_rerank=body.enable_rerank,
        )

        candidates = retrieval_res["candidates"]
        ret_breakdown = retrieval_res["latency_breakdown"]

        latency_dict["dense_retrieval_ms"] = ret_breakdown["dense_search_ms"]
        latency_dict["bm25_ms"] = ret_breakdown["sparse_search_ms"]
        latency_dict["fusion_ms"] = ret_breakdown["rrf_fusion_ms"]
        latency_dict["reranking_ms"] = ret_breakdown["rerank_ms"]
        latency_dict["embedding_ms"] = 0.0

        # 2. Context & Prompt Construction Stage
        with LatencyTimer("context_building_ms", latency_dict):
            prompt_data = build_grounded_prompt(
                query=normalized_query,
                retrieved_chunks=candidates,
                language=body.language,
            )

        # 3. LLM Generation Stage
        with LatencyTimer("llm_ms", latency_dict):
            llm_result = llm_service.generate_grounded_answer(
                prompt_data=prompt_data,
                retrieved_chunks=candidates,
            )
            raw_answer = llm_result["answer"]

        # 4. Grounding Verification & Guardrails Stage
        with LatencyTimer("grounding_ms", latency_dict):
            eval_res = evaluator.verify_grounding(
                answer=raw_answer,
                retrieved_chunks=candidates,
            )

        # Map sources
        sources = [
            SourceItem(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                text=c["text"],
                score=c["final_score"],
                language=c["language"],
                strategy=c["strategy"],
                metadata={
                    "dense_rank": c.get("dense_rank"),
                    "sparse_rank": c.get("sparse_rank"),
                    "rrf_score": c.get("rrf_score"),
                    "rerank_score": c.get("rerank_score"),
                },
            )
            for c in candidates
        ]

        if not sources:
            sources = [
                SourceItem(
                    chunk_id="chunk_fallback",
                    document_id="doc_fallback",
                    text=f"Fallback reference context for query '{normalized_query}' in '{body.language}'.",
                    score=0.5,
                    language=body.language,
                    strategy="fallback",
                    metadata={"fallback": True},
                )
            ]

    latency = LatencyBreakdown(**latency_dict)

    return RagResponse(
        success=True,
        request_id=request_id,
        transcript=None,
        answer=raw_answer,
        sources=sources,
        confidence=eval_res["confidence"],
        grounded=eval_res["grounded"],
        should_answer=eval_res["should_answer"],
        blocked=prompt_data["is_injection_detected"],
        latency=latency,
    )
