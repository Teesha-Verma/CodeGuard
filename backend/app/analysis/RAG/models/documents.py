"""RAG document models.

Strongly-typed models for the complete RAG pipeline:
document representation, chunking, embedding, search results, and validation.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentMetadata(BaseModel):
    """Unified metadata extracted from YAML frontmatter.
    
    Normalizes both Schema A (security docs with `id`) and
    Schema B (python/framework docs with `knowledge_id`).
    """
    document_id: str = Field(description="Unique document identifier (from id or knowledge_id)")
    title: str
    category: str
    subcategory: str = ""
    document_type: str = ""
    chunk_type: str = ""
    embedding_title: str = ""
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    severity: Severity = Severity.MEDIUM
    priority: Priority = Priority.MEDIUM
    retrieval_priority: str = ""
    confidence: str = ""
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    source: str = ""
    source_url: str = ""
    canonical_url: str = ""
    version: str = ""
    source_version: str = ""
    last_updated: str = ""
    related: list[str] = Field(default_factory=list, description="Related CWEs, topics, or documents")
    related_topics: list[str] = Field(default_factory=list)
    related_documents: list[str] = Field(default_factory=list)
    raw_frontmatter: dict[str, Any] = Field(default_factory=dict, description="Original unparsed frontmatter")

    @classmethod
    def from_frontmatter(cls, fm: dict[str, Any]) -> DocumentMetadata:
        """Build normalized metadata from raw YAML frontmatter dict.
        
        Handles both Schema A (`id`, `language`, `framework`) and
        Schema B (`knowledge_id`, `languages`, `frameworks`, `database`).
        """
        # Normalize document_id
        doc_id = fm.get("id") or fm.get("knowledge_id") or fm.get("official_id") or str(uuid.uuid4())

        # Normalize language/languages -> list
        languages = fm.get("languages") or fm.get("language") or []
        if isinstance(languages, str):
            languages = [languages]

        # Normalize framework/frameworks -> list
        frameworks = fm.get("frameworks") or fm.get("framework") or []
        if isinstance(frameworks, str):
            frameworks = [frameworks]

        # Normalize database -> list
        databases = fm.get("databases") or fm.get("database") or []
        if isinstance(databases, str):
            databases = [databases]

        # Normalize severity
        severity_raw = str(fm.get("severity", "medium")).lower()
        try:
            severity = Severity(severity_raw)
        except ValueError:
            severity = Severity.MEDIUM

        # Normalize priority
        priority_raw = str(fm.get("priority", "medium")).lower()
        try:
            priority = Priority(priority_raw)
        except ValueError:
            priority = Priority.MEDIUM

        # Merge related fields
        related = list(fm.get("related", []) or [])
        related_topics = list(fm.get("related_topics", []) or [])
        related_documents = list(fm.get("related_documents", []) or [])

        # last_updated normalization
        last_updated = fm.get("last_updated", "")
        if isinstance(last_updated, date):
            last_updated = last_updated.isoformat()
        else:
            last_updated = str(last_updated) if last_updated else ""

        return cls(
            document_id=str(doc_id),
            title=str(fm.get("title", "")),
            category=str(fm.get("category", "")),
            subcategory=str(fm.get("subcategory", "")),
            document_type=str(fm.get("document_type", "")),
            chunk_type=str(fm.get("chunk_type", "")),
            embedding_title=str(fm.get("embedding_title", "")),
            languages=languages,
            frameworks=frameworks,
            databases=databases,
            severity=severity,
            priority=priority,
            retrieval_priority=str(fm.get("retrieval_priority", "")),
            confidence=str(fm.get("confidence", "")),
            tags=list(fm.get("tags", []) or []),
            keywords=list(fm.get("keywords", []) or []),
            aliases=list(fm.get("aliases", []) or []),
            source=str(fm.get("source", "")),
            source_url=str(fm.get("source_url", "")),
            canonical_url=str(fm.get("canonical_url", "")),
            version=str(fm.get("version", "")),
            source_version=str(fm.get("source_version", "")),
            last_updated=last_updated,
            related=related,
            related_topics=related_topics,
            related_documents=related_documents,
            raw_frontmatter=dict(fm),
        )


class KnowledgeDocument(BaseModel):
    """A complete parsed knowledge document."""
    metadata: DocumentMetadata
    body: str = Field(description="Markdown body text after frontmatter")
    sections: dict[str, str] = Field(default_factory=dict, description="Parsed section header -> content")
    source_path: str = Field(description="Absolute path to the source .md file")
    content_hash: str = Field(default="", description="SHA-256 hash of raw file content for change detection")

    @property
    def document_id(self) -> str:
        return self.metadata.document_id


class KnowledgeChunk(BaseModel):
    """A semantic chunk derived from a KnowledgeDocument."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    section_title: str = ""
    chunk_index: int = 0
    total_chunks: int = 0
    char_count: int = 0
    metadata: DocumentMetadata | None = None
    source_path: str = ""

    @model_validator(mode="after")
    def _set_char_count(self) -> KnowledgeChunk:
        if self.char_count == 0:
            self.char_count = len(self.content)
        return self


class EmbeddingDocument(BaseModel):
    """A chunk ready for or already embedded."""
    chunk_id: str
    document_id: str
    content: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    dimension: int = 0

    @model_validator(mode="after")
    def _set_dimension(self) -> EmbeddingDocument:
        if self.embedding and self.dimension == 0:
            self.dimension = len(self.embedding)
        return self


class SearchResult(BaseModel):
    """Result from a vector similarity search."""
    chunk_id: str
    document_id: str
    content: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    section_title: str = ""
    source_path: str = ""


class ValidationIssue(BaseModel):
    """A single validation issue found in a document."""
    field: str
    message: str
    severity: str = "warning"  # warning | error


class ValidationResult(BaseModel):
    """Result of validating a knowledge document."""
    document_path: str
    is_valid: bool = True
    issues: list[ValidationIssue] = Field(default_factory=list)
    metadata_present: bool = False
    sections_found: list[str] = Field(default_factory=list)

    def add_error(self, field: str, message: str) -> None:
        self.issues.append(ValidationIssue(field=field, message=message, severity="error"))
        self.is_valid = False

    def add_warning(self, field: str, message: str) -> None:
        self.issues.append(ValidationIssue(field=field, message=message, severity="warning"))
