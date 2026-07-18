"""
CodeGuard — Configuration management.

Uses Pydantic Settings for environment-based configuration.
Reads from .env file with fallback defaults for development.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "CodeGuard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database (PostgreSQL) ────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "codeguard"
    POSTGRES_USER: str = "codeguard"
    POSTGRES_PASSWORD: str = "codeguard"
    DATABASE_URL: Optional[str] = None

    @model_validator(mode="after")
    def _assemble_database_url(self) -> "Settings":
        """Auto-construct DATABASE_URL from POSTGRES_* components if not set."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    # ── LLM ──────────────────────────────────────────────────────
    LLM_PROVIDER: str = "groq"  # "groq" | "openai"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
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

    # ── Confidence Weights ───────────────────────────────────────
    CONFIDENCE_BASE_SCORE: float = 0.40
    CONFIDENCE_LINTER_AST_OVERLAP: float = 0.30
    CONFIDENCE_HIGH_PRIORITY_BONUS: float = 0.15
    CONFIDENCE_LOW_SIGNAL_PENALTY: float = -0.15
    CONFIDENCE_TEST_FILE_DISCOUNT: float = -0.15
    CONFIDENCE_CONFIG_FILE_DISCOUNT: float = -0.10
    CONFIDENCE_HIGH_PRECISION_AST_BONUS: float = 0.15
    CONFIDENCE_CHANGED_CODE_BOOST: float = 0.15

    # ── Maintainability Thresholds ───────────────────────────────
    CYCLOMATIC_COMPLEXITY_MAX: int = 10
    MAINTAINABILITY_INDEX_MIN: int = 65
    MAX_NESTING_DEPTH: int = 3
    REASONING_ACTIVATION_THRESHOLD: float = 0.50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
