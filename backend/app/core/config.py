"""
CodeGuard V2 — Configuration management.

Uses Pydantic Settings for environment-based configuration.
Reads from .env file with fallback defaults for development.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "CodeGuard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # ── Database (PostgreSQL) ────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "codeguard"
    POSTGRES_USER: str = "codeguard"
    POSTGRES_PASSWORD: str = "codeguard"
    DATABASE_URL: Optional[str] = None
    ALEMBIC_DATABASE_URL: Optional[str] = None

    # ── Database Connection Pooling ─────────────────────────────
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    @model_validator(mode="after")
    def _assemble_database_url(self) -> "Settings":
        """Auto-construct or normalize DATABASE_URL and ALEMBIC_DATABASE_URL."""
        if self.DATABASE_URL:
            # Normalize legacy postgres:// to postgresql:// for SQLAlchemy 2.0 compatibility
            if self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = "postgresql://" + self.DATABASE_URL[len("postgres://"):]
        else:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        if self.ALEMBIC_DATABASE_URL and self.ALEMBIC_DATABASE_URL.startswith("postgres://"):
            self.ALEMBIC_DATABASE_URL = "postgresql://" + self.ALEMBIC_DATABASE_URL[len("postgres://"):]

        return self

    @property
    def effective_alembic_url(self) -> str:
        """Return ALEMBIC_DATABASE_URL if set, otherwise fall back to DATABASE_URL."""
        return self.ALEMBIC_DATABASE_URL or self.DATABASE_URL or ""

    def get_masked_database_url(self, url: Optional[str] = None) -> str:
        """Return a sanitized database URL with password masked for safe logging."""
        import re
        target = url or self.DATABASE_URL
        if not target:
            return ""
        return re.sub(r":([^:@/]+)@", r":***@", target)

    # ── GitHub ───────────────────────────────────────────────────
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_URL: str = "https://api.github.com"
    GITHUB_TIMEOUT: int = 30
    E2E_GITHUB_OWNER: Optional[str] = None
    E2E_GITHUB_REPO: Optional[str] = None
    E2E_GITHUB_PR_NUMBER: Optional[int] = None

    # ── Groq (LLM Reasoning & Generation) ─────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_PRIMARY_MODEL: str = "openai/gpt-oss-120b"
    GROQ_LLM_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODELS: str = "qwen/qwen3.8-27b,groq/compound-mini,llama-3.3-70b-versatile,llama-3.1-8b-instant"
    GROQ_TIMEOUT: int = 60
    GROQ_MAX_RETRIES: int = 2
    GROQ_REAL_TEST: bool = False

    # ── Gemini (LLM Reasoning & Generation) ───────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_PRIMARY_MODEL: str = "gemini-3.5-flash"
    GEMINI_LLM_MODEL: str = "gemini-3.5-flash"
    GEMINI_LLM_FALLBACK_MODELS: str = "gemini-3.5-flash-lite,gemini-3.6-flash"
    GEMINI_FALLBACK_MODELS: str = "gemini-3.5-flash-lite,gemini-3.6-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_API_BASE_URL: str = "https://generativelanguage.googleapis.com"
    GEMINI_TIMEOUT: int = 60
    GEMINI_MAX_RETRIES: int = 2

    # ── LLM Configuration ─────────────────────────────────────────
    LLM_PROVIDER: str = "groq"  # "groq" | "gemini" | "mock" | "openai"
    LLM_FALLBACK_PROVIDERS: str = "gemini"  # comma-separated e.g. "gemini" or "groq"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_API_KEY: str = ""
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 2
    LLM_MAX_GENERATION_REQUESTS_PER_REVIEW: int = 25
    LLM_MAX_CONTEXT_LINES: int = 50
    LLM_MAX_CONTEXT_CHARS: int = 4000
    LLM_BACKOFF_BASE_SECONDS: float = 1.5
    LLM_CACHE_ENABLED: bool = True
    LLM_CACHE_TTL: int = 3600
    GEMINI_REAL_TEST: bool = False

    @property
    def fallback_provider_list(self) -> list[str]:
        """Return parsed list of fallback LLM providers."""
        if not self.LLM_FALLBACK_PROVIDERS:
            return []
        if isinstance(self.LLM_FALLBACK_PROVIDERS, str):
            return [p.strip().lower() for p in self.LLM_FALLBACK_PROVIDERS.split(",") if p.strip()]
        return [str(p).lower() for p in self.LLM_FALLBACK_PROVIDERS]

    @property
    def groq_fallback_model_list(self) -> list[str]:
        """Return parsed list of Groq fallback models."""
        if isinstance(self.GROQ_FALLBACK_MODELS, str):
            return [m.strip() for m in self.GROQ_FALLBACK_MODELS.split(",") if m.strip()]
        return list(self.GROQ_FALLBACK_MODELS)

    @property
    def gemini_fallback_model_list(self) -> list[str]:
        """Return parsed list of Gemini fallback models."""
        fallback = self.GEMINI_LLM_FALLBACK_MODELS or getattr(self, "GEMINI_FALLBACK_MODELS", "")
        if isinstance(fallback, str):
            return [m.strip() for m in fallback.split(",") if m.strip()]
        return list(fallback)

    # ── RAG ──────────────────────────────────────────────────────
    RAG_ENABLED: bool = True
    RAG_EMBEDDING_PROVIDER: str = "gemini"
    RAG_EMBEDDING_MODEL: str = "gemini-embedding-2"
    RAG_TOP_K: int = 10
    RAG_RERANK_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.70
    RAG_MAX_CONTEXT_CHUNKS: int = 10
    RAG_MAX_CONTEXT_TOKENS: int = 8000
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 150
    RAG_CACHE_ENABLED: bool = True
    RAG_CACHE_TTL: int = 3600
    RAG_VECTOR_STORE: str = "memory"
    RAG_KNOWLEDGE_PATH: str = "app/analysis/RAG/knowledge"

    def get_resolved_knowledge_path(self) -> str:
        """Resolve knowledge path to an existing absolute directory."""
        import os
        from pathlib import Path
        candidate = Path(self.RAG_KNOWLEDGE_PATH)
        if candidate.is_dir():
            return str(candidate.resolve())
        # Fallback to backend/app/analysis/RAG/knowledge
        backend_dir = Path(__file__).resolve().parent.parent.parent
        app_rag_kb = backend_dir / "app" / "analysis" / "RAG" / "knowledge"
        if app_rag_kb.is_dir():
            return str(app_rag_kb)
        return str(candidate)

    # ── Embeddings ───────────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIMENSION: int = 768
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_TIMEOUT: int = 60
    EMBEDDING_MAX_RETRIES: int = 3

    # ── Analysis ─────────────────────────────────────────────────
    MAX_FILE_SIZE_KB: int = 500
    MAX_DIFF_FILES: int = 50
    CONTEXT_WINDOW_LINES: int = 10
    AST_ENABLED: bool = True
    CFG_ENABLED: bool = True
    CALL_GRAPH_ENABLED: bool = True
    DATAFLOW_ENABLED: bool = True
    REPOSITORY_INTELLIGENCE_ENABLED: bool = True
    LINTERS_ENABLED: bool = True

    # ── Static Analysis ──────────────────────────────────────────
    PYLINT_ENABLED: bool = True
    FLAKE8_ENABLED: bool = True
    BANDIT_ENABLED: bool = True
    LINTER_TIMEOUT: int = 15
    REPOSITORY_ANALYSIS_TIMEOUT: int = 30

    # ── Pipeline ─────────────────────────────────────────────────
    PIPELINE_TIMEOUT: int = 300
    MAX_REVIEW_DURATION_SECONDS: int = 300
    GIT_TIMEOUT: int = 60
    LLM_STAGE_TIMEOUT: int = 60
    PIPELINE_MAX_WORKERS: int = 4
    BACKGROUND_TASKS_ENABLED: bool = True

    # ── Storage ──────────────────────────────────────────────────
    REPOS_DIR: str = "repos"
    DATA_DIR: str = "data"
    REVIEW_DATA_DIR: str = "data/reviews"
    LOG_DIR: str = "logs"

    # ── Observability ────────────────────────────────────────────
    TRACE_ENABLED: bool = True
    LLM_TELEMETRY_ENABLED: bool = True
    TRACE_LOG_LEVEL: str = "INFO"

    # ── Evaluation ───────────────────────────────────────────────
    EVALUATION_ENABLED: bool = True
    GOLDEN_DATASET_PATH: str = "data/evaluation"
    EVALUATION_OUTPUT_PATH: str = "data/evaluation/results"

    # ── Security ─────────────────────────────────────────────────
    API_AUTH_ENABLED: bool = False

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

    @model_validator(mode="after")
    def _validate_configuration(self) -> "Settings":
        """Validate LLM and embedding configurations."""
        # Align LLM_API_KEY with GROQ_API_KEY if using Groq
        if self.LLM_PROVIDER == "groq":
            if not self.GROQ_API_KEY and self.LLM_API_KEY:
                self.GROQ_API_KEY = self.LLM_API_KEY
            elif self.GROQ_API_KEY and not self.LLM_API_KEY:
                self.LLM_API_KEY = self.GROQ_API_KEY
            if self.GROQ_LLM_MODEL != self.LLM_MODEL:
                if self.LLM_MODEL == "llama-3.3-70b-versatile":
                    self.LLM_MODEL = self.GROQ_LLM_MODEL
                else:
                    self.GROQ_LLM_MODEL = self.LLM_MODEL

        # Align GEMINI_EMBEDDING_MODEL with EMBEDDING_MODEL
        if self.GEMINI_EMBEDDING_MODEL != self.EMBEDDING_MODEL:
            self.GEMINI_EMBEDDING_MODEL = self.EMBEDDING_MODEL

        return self

    def validate_groq_credentials(self) -> None:
        """Validate that Groq API credentials exist when required at runtime."""
        effective_key = self.GROQ_API_KEY or self.LLM_API_KEY or os.environ.get("GROQ_API_KEY")
        if not effective_key or effective_key in ("your_groq_api_key_here", "mock_key"):
            raise ValueError(
                "Groq API key is required when Groq LLM functionality is enabled."
            )

    def validate_gemini_credentials(self) -> None:
        """Validate that Gemini API credentials exist for embeddings at runtime."""
        effective_key = self.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not effective_key or effective_key in ("your_gemini_api_key_here", "mock_key"):
            raise ValueError(
                "Gemini API key is required for Gemini embeddings."
            )

    def validate_gemini_llm_credentials(self) -> None:
        """Validate that Gemini API credentials exist for Gemini LLM reasoning at runtime."""
        effective_key = self.GEMINI_API_KEY or self.LLM_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
        if not effective_key or effective_key in ("your_gemini_api_key_here", "mock_key"):
            raise ValueError(
                "Gemini API key is required when Gemini LLM functionality is enabled."
            )

    model_config = {
        "env_file": str(_env_path),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
