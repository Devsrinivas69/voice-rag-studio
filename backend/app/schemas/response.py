from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LatencyBreakdown(BaseModel):
    audio_validation_ms: Optional[float] = None
    stt_ms: Optional[float] = None
    query_normalization_ms: Optional[float] = None
    routing_ms: Optional[float] = None
    embedding_ms: Optional[float] = None
    dense_retrieval_ms: Optional[float] = None
    bm25_ms: Optional[float] = None
    fusion_ms: Optional[float] = None
    reranking_ms: Optional[float] = None
    context_building_ms: Optional[float] = None
    llm_ms: Optional[float] = None
    grounding_ms: Optional[float] = None
    total_backend_ms: float = 0.0


class SourceItem(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Source document identifier")
    text: str = Field(..., description="Retrieved passage snippet")
    score: float = Field(..., description="Combined fusion/rerank score")
    language: str = Field(default="en", description="Source language")
    strategy: str = Field(default="fixed", description="Chunking strategy used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")


class RagResponse(BaseModel):
    success: bool = True
    request_id: str = Field(..., description="Unique correlation request ID")
    transcript: Optional[str] = Field(default=None, description="STT transcript (present for voice queries)")
    answer: str = Field(..., description="Grounded answer text or refusal explanation")
    sources: List[SourceItem] = Field(default_factory=list, description="Retrieved context sources")
    confidence: float = Field(default=0.0, description="Overall answer confidence score [0.0 - 1.0]")
    grounded: bool = Field(default=True, description="Grounding verification status")
    should_answer: bool = Field(default=True, description="False if query refused due to low relevance/safety")
    blocked: bool = Field(default=False, description="True if request was blocked by safety/guardrails")
    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown, description="Measured stage-by-stage latencies in ms")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code identifier (e.g. STT_TIMEOUT, INVALID_AUDIO, OFFLINE)")
    message: str = Field(..., description="User-safe human readable error message")


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: str


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    mock_mode: bool


class ComponentStatus(BaseModel):
    qdrant: bool
    bm25: bool
    embedding_model: bool
    configuration: bool


class ReadyResponse(BaseModel):
    status: str = "ready"
    components: ComponentStatus
