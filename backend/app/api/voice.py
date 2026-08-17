from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from backend.app.config import Settings
from backend.app.dependencies import get_app_settings, get_request_id
from backend.app.monitoring.timer import LatencyTimer
from backend.app.schemas.response import LatencyBreakdown, RagResponse, SourceItem
from backend.app.services.evaluator import GroundingEvaluator
from backend.app.services.llm import LLMService
from backend.app.services.prompts import build_grounded_prompt
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.sarvam import SarvamSTTService

router = APIRouter(prefix="/api/voice", tags=["Voice"])

_stt_service = None
_retriever = None
_llm_service = None
_evaluator = None


def get_stt_service() -> SarvamSTTService:
    global _stt_service
    if _stt_service is None:
        _stt_service = SarvamSTTService()
    return _stt_service


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


ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}


@router.post("/query", response_model=RagResponse)
async def voice_query(
    audio: UploadFile = File(..., description="Uploaded microphone audio blob"),
    language: str = Form("kn-IN", description="Indic language code (e.g. kn-IN, hi-IN, ta-IN, en-IN)"),
    top_k: int = Form(10, description="Top K retrieval candidates count"),
    enable_rerank: bool = Form(False, description="Enable cross-encoder reranking stage"),
    settings: Settings = Depends(get_app_settings),
    request_id: str = Depends(get_request_id),
    stt_service: SarvamSTTService = Depends(get_stt_service),
    retriever: HybridRetriever = Depends(get_retriever),
    llm_service: LLMService = Depends(get_llm_service),
    evaluator: GroundingEvaluator = Depends(get_evaluator),
) -> RagResponse:
    """POST /api/voice/query — Voice input RAG endpoint with Sarvam STT, hybrid retrieval, Gemini LLM, and grounding verification."""
    latency_dict = {}

    with LatencyTimer("total_backend_ms", latency_dict):
        # 1. Audio validation
        with LatencyTimer("audio_validation_ms", latency_dict):
            filename = audio.filename or "audio.wav"
            ext = "." + filename.split(".")[-1].lower() if "." in filename else ".wav"

            contents = await audio.read()
            if len(contents) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "EMPTY_AUDIO", "message": "Uploaded audio file is empty (0 bytes)."},
                )

            max_size_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
            if len(contents) > max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "code": "AUDIO_TOO_LARGE",
                        "message": f"Audio file size exceeds limit of {settings.MAX_AUDIO_SIZE_MB}MB.",
                    },
                )

        # 2. Sarvam Saaras v3 STT Transcription
        stt_result = await stt_service.transcribe_audio(
            audio_bytes=contents,
            filename=filename,
            language=language,
        )
        transcript = stt_result["transcript"]
        latency_dict["stt_ms"] = stt_result["stt_ms"]

        # 3. Query normalization & RAG execution
        with LatencyTimer("query_normalization_ms", latency_dict):
            query_text = transcript.strip()

        with LatencyTimer("routing_ms", latency_dict):
            route = "DATASET"

        retrieval_res = retriever.retrieve(
            query=query_text,
            language=language,
            top_k=top_k,
            enable_rerank=enable_rerank,
        )

        candidates = retrieval_res["candidates"]
        ret_breakdown = retrieval_res["latency_breakdown"]

        latency_dict["dense_retrieval_ms"] = ret_breakdown["dense_search_ms"]
        latency_dict["bm25_ms"] = ret_breakdown["sparse_search_ms"]
        latency_dict["fusion_ms"] = ret_breakdown["rrf_fusion_ms"]
        latency_dict["reranking_ms"] = ret_breakdown["rerank_ms"]
        latency_dict["embedding_ms"] = 0.0

        # 4. Context & Prompt Construction Stage
        with LatencyTimer("context_building_ms", latency_dict):
            prompt_data = build_grounded_prompt(
                query=query_text,
                retrieved_chunks=candidates,
                language=language,
            )

        # 5. LLM Generation Stage
        with LatencyTimer("llm_ms", latency_dict):
            llm_result = llm_service.generate_grounded_answer(
                prompt_data=prompt_data,
                retrieved_chunks=candidates,
            )
            raw_answer = llm_result["answer"]

        # 6. Grounding Verification Stage
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
                    text=f"Fallback reference context for transcribed query '{query_text}' in '{language}'.",
                    score=0.5,
                    language=language,
                    strategy="fallback",
                    metadata={"fallback": True},
                )
            ]

    latency = LatencyBreakdown(**latency_dict)

    return RagResponse(
        success=True,
        request_id=request_id,
        transcript=transcript,
        answer=raw_answer,
        sources=sources,
        confidence=eval_res["confidence"],
        grounded=eval_res["grounded"],
        should_answer=eval_res["should_answer"],
        blocked=prompt_data["is_injection_detected"],
        latency=latency,
    )
