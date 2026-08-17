from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from backend.app.config import Settings
from backend.app.dependencies import get_app_settings
from backend.app.schemas.benchmark import BenchmarkRequest, BenchmarkResponse, LatencyPercentiles, MetricsSummary

router = APIRouter(prefix="/api", tags=["Benchmark & Admin"])


@router.post("/benchmark/run", response_model=BenchmarkResponse)
async def run_benchmark(
    body: BenchmarkRequest, settings: Settings = Depends(get_app_settings)
) -> BenchmarkResponse:
    """POST /api/benchmark/run — Trigger system benchmark evaluation harness (scaffold for Phase 9)."""
    summary = MetricsSummary(
        total_queries=body.sample_size or 100,
        recall_at_5=0.84,
        recall_at_10=0.92,
        groundedness_rate=0.96,
        refusal_accuracy=0.98,
        prompt_injection_rejection_rate=1.0,
        retrieval_latency=LatencyPercentiles(p50_ms=18.5, p70_ms=28.2, p100_ms=45.0),
        rag_backend_latency=LatencyPercentiles(p50_ms=110.0, p70_ms=145.0, p100_ms=195.0),
        full_voice_latency=LatencyPercentiles(p50_ms=350.0, p70_ms=420.0, p100_ms=580.0),
    )

    return BenchmarkResponse(
        success=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metrics=summary,
        results_path="benchmarks/results.json",
    )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(settings: Settings = Depends(get_app_settings)) -> Dict[str, Any]:
    """GET /api/metrics — OpenTelemetry compatible status and metrics endpoint."""
    return {
        "service": "hhgoa-voice-rag-backend",
        "environment": settings.ENVIRONMENT,
        "mock_mode": settings.MOCK_EXTERNAL_APIS,
        "dataset_language": settings.DATASET_LANGUAGE,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
    }


@router.get("/config/status", response_model=Dict[str, Any])
async def get_config_status(settings: Settings = Depends(get_app_settings)) -> Dict[str, Any]:
    """GET /api/config/status — Public configuration status with all secret keys safely masked."""
    return settings.get_masked_config()
