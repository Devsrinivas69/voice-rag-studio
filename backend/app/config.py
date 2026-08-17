import os
from functools import lru_cache
from typing import Any, Dict, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # API Keys & Provider Config
    SARVAM_API_KEY: Optional[str] = Field(default=None, description="Sarvam AI API Key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini LLM model name")

    # Qdrant Config
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant cluster or local URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant Cloud API key (optional for local)")
    QDRANT_COLLECTION: str = Field(default="msmarco_xi", description="Qdrant collection name")

    # Models & API Integrations
    EMBEDDING_MODEL: str = Field(
        default="models/gemini-embedding-2",
        description="Gemini Embedding 2 model for dense vector representations (768 dim)",
    )
    LLM_MODEL: str = Field(
        default="gemini-3.7-flash",
        description="Gemini Generation Model ID for answer synthesis",
    )
    RERANKER_MODEL: str = Field(default="BAAI/bge-reranker-v2-m3", description="Reranker cross-encoder model")
    RERANKER_ENABLED: bool = Field(default=True, description="Enable reranking step")

    # Dataset Config
    DATASET_NAME: str = Field(default="ai4bharat/MSMARCO-XI", description="Hugging Face dataset identifier")
    DATASET_LANGUAGE: str = Field(default="kn", description="Target language code (e.g. kn, hi, ta, en)")
    DATASET_SPLIT: str = Field(default="validation", description="Dataset split (validation/train)")
    DATASET_SAMPLE_SIZE: int = Field(default=5000, description="Sample size for ingestion in development")
    FULL_INGEST: bool = Field(default=False, description="Explicit flag required for full dataset ingestion")

    # Retrieval Thresholds
    TOP_K_DENSE: int = Field(default=20, description="Number of dense vector search results")
    TOP_K_RETRIEVAL: int = Field(default=10, description="Default number of retrieval candidates")
    TOP_K_BM25: int = Field(default=20, description="Number of BM25 lexical search results")
    TOP_K_RERANK: int = Field(default=10, description="Number of candidates to pass to reranker")
    FINAL_CONTEXT_K: int = Field(default=5, description="Number of final context chunks passed to LLM")
    RRF_K: int = Field(default=60, description="RRF constant score parameter")

    # Chunking Config
    CHUNK_SIZE: int = Field(default=512, description="Target chunk size in tokens")
    CHUNK_OVERLAP: int = Field(default=128, description="Chunk overlap in tokens")
    SEMANTIC_CHUNKING_ENABLED: bool = Field(default=True, description="Enable semantic chunker")
    SEMANTIC_BREAKPOINT_THRESHOLD: float = Field(default=0.75, description="Breakpoint similarity threshold")

    # Guardrails Config
    LLM_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")
    LOW_RELEVANCE_THRESHOLD: float = Field(default=0.35, description="Minimum relevance score to attempt LLM answer")
    GROUNDING_THRESHOLD: float = Field(default=0.70, description="Minimum confidence for grounding verification")

    # Audio Limits
    MAX_AUDIO_SECONDS: int = Field(default=30, description="Maximum allowed audio duration in seconds")
    MAX_AUDIO_SIZE_MB: int = Field(default=10, description="Maximum allowed audio file size in MB")

    # Network & Retries
    REQUEST_TIMEOUT_SECONDS: int = Field(default=10, description="External request timeout in seconds")
    MAX_RETRIES: int = Field(default=2, description="Maximum retry attempts for transient API errors")

    # App Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="CORS allowed origin URL")

    # Mode Flags
    MOCK_EXTERNAL_APIS: bool = Field(default=True, description="Use mock mode for Sarvam & Gemini when keys absent")
    DEBUG: bool = Field(default=False, description="Enable debug logging")

    def validate_production_keys(self) -> None:
        """Fails startup if real API keys are missing when MOCK_EXTERNAL_APIS is False."""
        if not self.MOCK_EXTERNAL_APIS:
            missing = []
            if not self.SARVAM_API_KEY:
                missing.append("SARVAM_API_KEY")
            if not self.GEMINI_API_KEY:
                missing.append("GEMINI_API_KEY")
            if missing:
                raise ValueError(
                    f"Configuration Error: Missing required secrets [{', '.join(missing)}] "
                    f"when MOCK_EXTERNAL_APIS is False. Set MOCK_EXTERNAL_APIS=true for local dev without keys."
                )

    def get_masked_config(self) -> Dict[str, Any]:
        """Returns a sanitized dict of configuration parameters with API keys masked."""
        config_dict = self.model_dump()
        sensitive_keys = {"SARVAM_API_KEY", "GEMINI_API_KEY", "QDRANT_API_KEY"}
        masked: Dict[str, Any] = {}
        for key, val in config_dict.items():
            if key in sensitive_keys:
                if val and isinstance(val, str):
                    masked[key] = f"{val[:4]}...{val[-4:]}" if len(val) >= 8 else "****"
                else:
                    masked[key] = None
            else:
                masked[key] = val
        return masked


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_keys()
    return settings
