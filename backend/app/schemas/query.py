from typing import Optional
from pydantic import BaseModel, Field


class TextQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Text question to query against the dataset")
    language: str = Field(default="kn", description="Language code (e.g. kn, hi, ta, en)")
    top_k: int = Field(default=10, ge=1, le=100, description="Top K retrieval candidates count")
    enable_rerank: bool = Field(default=False, description="Enable cross-encoder reranking stage")


class VoiceQueryMetadata(BaseModel):
    language: str = Field(default="kn", description="Target transcription and response language code")
