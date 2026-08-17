import uuid
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.benchmark import router as benchmark_router
from backend.app.api.health import router as health_router
from backend.app.api.query import router as query_router
from backend.app.api.voice import router as voice_router
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger, request_id_ctx
from backend.app.schemas.response import ErrorDetail, StandardErrorResponse

settings = get_settings()

app = FastAPI(
    title="HHGOA 2026 — Voice-Enabled RAG API",
    description="Production-quality multilingual Voice Retrieval-Augmented Generation backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow CORS for Next.js frontend on Vercel and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """GET / — Service welcome and health endpoint."""
    return {
        "status": "online",
        "service": "HHGOA 2026 — Voice-Enabled RAG API",
        "version": "1.0.0",
        "health": "/health",
        "docs": "/docs",
    }


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Correlation ID middleware: assigns or propagates X-Request-ID across log contexts."""
    req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = req_id
    token = request_id_ctx.set(req_id)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_ctx.reset(token)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", "unknown")
    code = "HTTP_ERROR"
    message = str(exc.detail)

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", code)
        message = exc.detail.get("message", message)

    logger.warning(f"HTTPException [{exc.status_code}]: {message}", extra={"request_id": req_id})

    error_payload = StandardErrorResponse(
        success=False,
        error=ErrorDetail(code=code, message=message),
        request_id=req_id,
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True, extra={"request_id": req_id})

    error_payload = StandardErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please try again later.",
        ),
        request_id=req_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )


# Include API Routers
app.include_router(health_router)
app.include_router(query_router)
app.include_router(voice_router)
app.include_router(benchmark_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
