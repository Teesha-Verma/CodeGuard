"""RAG pipeline configuration.

Centralized settings with sensible defaults. All values can be overridden.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# Base path computation
_RAG_DIR = Path(__file__).resolve().parent.parent  # .../app/analysis/RAG
_DEFAULT_KNOWLEDGE_DIR = str(_RAG_DIR / "knowledge")


@dataclass
class ChunkingConfig:
    """Chunking parameters."""
    max_chunk_size: int = 1500
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    preserve_sections: bool = True
    include_metadata_header: bool = True


@dataclass
class EmbeddingConfig:
    """Embedding provider configuration."""
    provider: str = "mock"  # mock | gemini | openai
    model: str = "models/text-embedding-004"
    dimension: int = 768
    batch_size: int = 64
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    rate_limit_rpm: int = 1500


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    provider: str = "memory"  # memory | faiss | pgvector | chroma
    index_path: str = ""
    dimension: int = 768
    similarity_metric: str = "cosine"  # cosine | l2 | inner_product


@dataclass
class RAGConfig:
    """Top-level RAG pipeline configuration."""
    knowledge_dir: str = _DEFAULT_KNOWLEDGE_DIR
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    log_level: str = "INFO"
    supported_extensions: list[str] = field(default_factory=lambda: [".md"])

    @classmethod
    def from_env(cls) -> RAGConfig:
        """Build config from environment variables."""
        config = cls()
        config.knowledge_dir = os.environ.get("RAG_KNOWLEDGE_DIR", config.knowledge_dir)
        config.embedding.provider = os.environ.get("RAG_EMBEDDING_PROVIDER", config.embedding.provider)
        config.embedding.model = os.environ.get("RAG_EMBEDDING_MODEL", config.embedding.model)
        config.vector_store.provider = os.environ.get("RAG_VECTOR_STORE_PROVIDER", config.vector_store.provider)
        config.log_level = os.environ.get("RAG_LOG_LEVEL", config.log_level)
        dim = os.environ.get("RAG_EMBEDDING_DIMENSION")
        if dim:
            config.embedding.dimension = int(dim)
            config.vector_store.dimension = int(dim)
        return config
