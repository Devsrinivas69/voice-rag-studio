import contextvars
import json
import logging
import sys
import time
from typing import Any, Dict, Optional

# ContextVar for request correlation ID
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON without exposing secrets or raw user audio."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get() or getattr(record, "request_id", None) or "system",
        }

        if hasattr(record, "stage"):
            log_data["stage"] = record.stage
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "hhgoa_voice_rag", level: int = logging.INFO) -> logging.Logger:
    """Configures structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger


logger = setup_logger()
