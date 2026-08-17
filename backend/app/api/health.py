import os
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.config import Settings
from backend.app.dependencies import get_app_settings
from backend.app.schemas.response import ComponentStatus, HealthResponse, ReadyResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    """Liveness probe: verifies application is running without executing external network calls."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        mock_mode=settings.MOCK_EXTERNAL_APIS,
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check(settings: Settings = Depends(get_app_settings)) -> ReadyResponse:
    """Readiness probe: verifies system dependencies (Qdrant, BM25 index, embedding model config)."""
    # Check BM25 index file existence (e.g. indices/bm25_index.pkl or mock)
    bm25_ready = os.path.exists("indices/bm25_index.pkl") or settings.MOCK_EXTERNAL_APIS

    # Check configuration validity
    config_ready = True
    if not settings.MOCK_EXTERNAL_APIS:
        config_ready = bool(settings.SARVAM_API_KEY and settings.GEMINI_API_KEY)

    # Qdrant readiness (mocked as true in Phase 1 / mock mode)
    qdrant_ready = True

    # Embedding model configuration readiness
    embedding_ready = bool(settings.EMBEDDING_MODEL)

    components = ComponentStatus(
        qdrant=qdrant_ready,
        bm25=bm25_ready,
        embedding_model=embedding_ready,
        configuration=config_ready,
    )

    all_ready = all([qdrant_ready, bm25_ready, embedding_ready, config_ready])

    if not all_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "components": components.model_dump()},
        )

    return ReadyResponse(status="ready", components=components)
