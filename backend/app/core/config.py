"""
CodeGuard — Configuration management.

Uses Pydantic Settings for environment-based configuration.
Reads from .env file with fallback defaults for development.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "CodeGuard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────
    # SQLite for dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./codeguard.db"

    # ── LLM ──────────────────────────────────────────────────────
    LLM_PROVIDER: str = "gemini"  # "gemini" | "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60

    # ── GitHub ───────────────────────────────────────────────────
    GITHUB_TOKEN: Optional[str] = None

    # ── Paths ────────────────────────────────────────────────────
    REPOS_DIR: str = "repos"
    LOG_DIR: str = "logs"

    # ── Pipeline ─────────────────────────────────────────────────
    MAX_FILE_SIZE_KB: int = 500
    CONTEXT_WINDOW_LINES: int = 10
    MAX_DIFF_FILES: int = 50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
