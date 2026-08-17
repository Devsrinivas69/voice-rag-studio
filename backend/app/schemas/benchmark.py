from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkRequest(BaseModel):
    sample_size: Optional[int] = Field(default=100, description="Number of queries to evaluate")
    reranking_enabled: bool = Field(default=True, description="Compare with vs without reranker")


class LatencyPercentiles(BaseModel):
    p50_ms: float
    p70_ms: float
    p100_ms: float


class MetricsSummary(BaseModel):
    total_queries: int
    recall_at_5: float
    recall_at_10: float
    groundedness_rate: float
    refusal_accuracy: float
    prompt_injection_rejection_rate: float
    retrieval_latency: LatencyPercentiles
    rag_backend_latency: LatencyPercentiles
    full_voice_latency: LatencyPercentiles


class BenchmarkResponse(BaseModel):
    success: bool = True
    timestamp: str
    metrics: MetricsSummary
    results_path: str = "benchmarks/results.json"
