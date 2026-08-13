"""Structured logging for the RAG pipeline."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Get a logger namespaced under 'rag'."""
    return logging.getLogger(f"rag.{name}")


@dataclass
class PipelineStats:
    """Accumulated statistics for a pipeline run."""
    files_discovered: int = 0
    files_parsed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    validation_errors: int = 0
    validation_warnings: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    vectors_stored: int = 0
    total_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_discovered": self.files_discovered,
            "files_parsed": self.files_parsed,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "chunks_created": self.chunks_created,
            "embeddings_generated": self.embeddings_generated,
            "vectors_stored": self.vectors_stored,
            "total_time_ms": round(self.total_time_ms, 2),
            "error_count": len(self.errors),
        }


@contextmanager
def timed_operation(logger: logging.Logger, operation: str):
    """Context manager that logs operation duration."""
    start = time.monotonic()
    logger.info("Starting: %s", operation)
    try:
        yield
    except Exception:
        elapsed = (time.monotonic() - start) * 1000
        logger.error("Failed: %s after %.1f ms", operation, elapsed)
        raise
    else:
        elapsed = (time.monotonic() - start) * 1000
        logger.info("Completed: %s in %.1f ms", operation, elapsed)
