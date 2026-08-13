"""
Pydantic models for the Knowledge & RAG Layer.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.analysis.knowledge.constants import (
    DocumentCategory,
    DEFAULT_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    MAX_TOP_K,
)

def _utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)

class KnowledgeDocument(BaseModel):
    """Represents a complete knowledge document before chunking."""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: DocumentCategory
    source: str
    tags: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    language: str = "en"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

class KnowledgeChunk(BaseModel):
    """A single chunk derived from a KnowledgeDocument."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int
    category: DocumentCategory
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: int = 0

class EmbeddingResult(BaseModel):
    """Result from embedding generation."""
    chunk_id: str
    embedding: list[float]
    model: str
    dimension: int
    
    @model_validator(mode="after")
    def validate_dimension(self) -> "EmbeddingResult":
        """Ensure the embedding vector matches the specified dimension."""
        if len(self.embedding) != self.dimension:
            raise ValueError(f"Embedding length {len(self.embedding)} does not match dimension {self.dimension}")
        return self

class RepositoryContext(BaseModel):
    """Stores repository intelligence metadata."""
    repository_url: str
    primary_language: str = "python"
    framework: str = ""
    dependencies: list[str] = Field(default_factory=list)
    architecture_summary: str = ""
    cfg_summary: dict[str, Any] = Field(default_factory=dict)
    call_graph_summary: dict[str, Any] = Field(default_factory=dict)
    data_flow_summary: dict[str, Any] = Field(default_factory=dict)
    project_metadata: dict[str, Any] = Field(default_factory=dict)
    indexed_at: datetime = Field(default_factory=_utcnow)

class RetrievalRequest(BaseModel):
    """Structured request for knowledge retrieval."""
    query: str
    top_k: int = Field(default=DEFAULT_TOP_K)
    categories: list[DocumentCategory] | None = None
    tags: list[str] | None = None
    similarity_threshold: float = Field(default=DEFAULT_SIMILARITY_THRESHOLD)
    repository_context: RepositoryContext | None = None
    
    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Validate top_k is within allowed range."""
        if v < 1 or v > MAX_TOP_K:
            raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
        return v
        
    @field_validator("similarity_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate similarity_threshold is between 0 and 1."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        return v

class RetrievalResult(BaseModel):
    """A single result from retrieval."""
    chunk: KnowledgeChunk
    similarity_score: float
    rerank_score: float | None = None
    final_score: float
    source_document_title: str = ""

class RetrievedContext(BaseModel):
    """Final aggregated context returned by the query engine."""
    results: list[RetrievalResult]
    query: str
    total_results: int
    repository_context: RepositoryContext | None = None
    retrieval_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class MetadataRecord(BaseModel):
    """Record for metadata storage."""
    record_id: str
    document_id: str
    chunk_id: str | None = None
    category: DocumentCategory
    tags: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    source: str = ""
    created_at: datetime = Field(default_factory=_utcnow)
    extra: dict[str, Any] = Field(default_factory=dict)
