"""
CodeGuard — Structured logging with correlation ID support.

Provides JSON-formatted logs with review_id tracing for pipeline
observability. All pipeline stages log through this module.
"""

from __future__ import annotations

import logging
import json
import sys
import os
import re
from datetime import datetime, timezone
from typing import Optional

from app.core.config import get_settings


_SECRET_PATTERNS = [
    # Groq API keys
    (re.compile(r"gsk_[a-zA-Z0-9_\-]{15,}"), "gsk_***REDACTED***"),
    # Gemini API keys
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{20,}"), "AIzaSy***REDACTED***"),
    # GitHub personal access tokens
    (re.compile(r"ghp_[a-zA-Z0-9]{20,}"), "ghp_***REDACTED***"),
    (re.compile(r"github_pat_[a-zA-Z0-9_]{20,}"), "github_pat_***REDACTED***"),
    # Bearer tokens in Authorization headers or strings
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE), r"\1***REDACTED***"),
    # Passwords in URLs (PostgreSQL/database connection strings)
    (re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\1***REDACTED***\3"),
    # Explicit password assignments
    (re.compile(r"(password\s*[:=]\s*['\"]?)([^'\"\s&]+)(['\"]?)", re.IGNORECASE), r"\1***REDACTED***\3"),
    # Generic API key query parameters or assignments
    (re.compile(r"((?:api[_-]?key|secret[_-]?key|token)\s*[:=]\s*['\"]?)([^'\"\s&]{8,})(['\"]?)", re.IGNORECASE), r"\1***REDACTED***\3"),
]


def mask_secrets(text: str) -> str:
    """Sanitizes strings by masking API keys, passwords, and tokens."""
    if not text or not isinstance(text, str):
        return str(text or "")
    sanitized = text
    for pattern, replacement in _SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON for structured ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_secrets(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Attach correlation fields if present
        if hasattr(record, "review_id"):
            log_entry["review_id"] = record.review_id
        if hasattr(record, "stage"):
            log_entry["stage"] = record.stage
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Attach exception info (safely masked)
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = mask_secrets(self.formatException(record.exc_info))

        return json.dumps(log_entry, default=str)


def get_logger(
    name: str = "codeguard",
    review_id: Optional[str] = None,
) -> logging.Logger:
    """
    Create or retrieve a logger with JSON formatting.

    Args:
        name: Logger name (usually module path).
        review_id: Optional correlation ID for pipeline tracing.

    Returns:
        Configured Logger instance.
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logger.propagate = False

    # ── Console handler ──────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # ── File handler (optional) ──────────────────────────────────
    log_dir = settings.LOG_DIR
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "codeguard.log"),
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


class PipelineLogger:
    """
    Convenience wrapper that auto-attaches review_id and stage
    to every log call for pipeline traceability.
    """

    def __init__(self, review_id: str, stage: str = ""):
        self._logger = get_logger(f"codeguard.pipeline.{stage}")
        self.review_id = review_id
        self.stage = stage

    def _extra(self, **kwargs) -> dict:
        return {"review_id": self.review_id, "stage": self.stage, **kwargs}

    def info(self, msg: str, **kwargs):
        self._logger.info(msg, extra=self._extra(**kwargs))

    def warning(self, msg: str, **kwargs):
        self._logger.warning(msg, extra=self._extra(**kwargs))

    def error(self, msg: str, **kwargs):
        self._logger.error(msg, extra=self._extra(**kwargs))

    def debug(self, msg: str, **kwargs):
        self._logger.debug(msg, extra=self._extra(**kwargs))
