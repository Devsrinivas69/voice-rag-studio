from fastapi import Request
from backend.app.config import Settings, get_settings


def get_app_settings() -> Settings:
    """FastAPI dependency for accessing application settings."""
    return get_settings()


def get_request_id(request: Request) -> str:
    """FastAPI dependency for extracting the request correlation ID."""
    return getattr(request.state, "request_id", "unknown-request-id")
