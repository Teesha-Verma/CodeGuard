"""
Reusable chunking strategies for the Knowledge & RAG Layer.

Provides markdown-aware and code-aware chunking that produces
structured KnowledgeChunk objects with deterministic IDs.
"""

import hashlib
import logging
import re
from typing import List, Tuple

from app.analysis.knowledge.models import KnowledgeDocument, KnowledgeChunk
from app.analysis.knowledge.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
)

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Base chunking strategy."""

    def chunk(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """Chunk a document into a list of KnowledgeChunks."""
        raise NotImplementedError("Subclasses must implement chunk method")


class MarkdownChunker(ChunkingStrategy):
    """
    Markdown-aware chunking strategy.

    Splits on markdown headers (##, ###) first, then falls back to
    paragraph-level splitting, preserving metadata throughout.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_size < MIN_CHUNK_SIZE or chunk_size > MAX_CHUNK_SIZE:
            raise ValueError(
                f"chunk_size must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}, got {chunk_size}"
            )
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError(
                "overlap must be non-negative and less than chunk_size"
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """
        Chunk a KnowledgeDocument into KnowledgeChunk objects.

        Pipeline:
        1. Split on markdown headers
        2. If sections exceed chunk_size, split by paragraphs/words with overlap
        3. Generate deterministic chunk IDs
        4. Return structured KnowledgeChunk objects with proper offsets
        """
        logger.debug(
            "Chunking document '%s' (id=%s) using MarkdownChunker",
            document.title,
            document.document_id,
        )
        chunks: list[KnowledgeChunk] = []

        # 1. Split on markdown headers
        sections = self._split_by_headers(document.content)

        chunk_index = 0
        running_offset = 0

        for header, content in sections:
            full_text = f"{header}\n{content}".strip() if header else content.strip()

            if not full_text:
                continue

            # 2. If section > chunk_size, split further with overlap
            if len(full_text) > self.chunk_size:
                sub_chunks = self._split_with_overlap(full_text, self.chunk_size)
            else:
                sub_chunks = [full_text]

            for text_chunk in sub_chunks:
                if not text_chunk.strip():
                    continue

                chunk_id = self._generate_chunk_id(
                    document.document_id, chunk_index, text_chunk
                )

                start_offset = document.content.find(
                    text_chunk[:50], running_offset
                )
                if start_offset == -1:
                    start_offset = running_offset
                end_offset = start_offset + len(text_chunk)

                knowledge_chunk = KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    content=text_chunk,
                    chunk_index=chunk_index,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    category=document.category,
                    tags=list(document.tags),
                    metadata={"header": header, **(document.metadata or {})},
                    token_count=len(text_chunk.split()),
                )
                chunks.append(knowledge_chunk)
                running_offset = end_offset
                chunk_index += 1

        logger.debug(
            "Generated %d chunks for document '%s'", len(chunks), document.document_id
        )
        return chunks

    def _split_by_headers(self, text: str) -> list[tuple[str, str]]:
        """Split text by markdown headers, returning (header, content) pairs."""
        header_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
        parts = header_pattern.split(text)

        sections: list[tuple[str, str]] = []
        if parts:
            # First part is before any header
            if parts[0].strip():
                sections.append(("", parts[0]))

            # Subsequent parts are paired (header, content)
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i + 1] if i + 1 < len(parts) else ""
                sections.append((header, content))

        return sections

    def _split_with_overlap(self, text: str, max_size: int) -> list[str]:
        """Split text into chunks with configurable overlap."""
        words = text.split()
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > max_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Backtrack for overlap
                overlap_size = 0
                overlap_chunk: list[str] = []
                for w in reversed(current_chunk):
                    if overlap_size + len(w) + 1 > self.overlap:
                        break
                    overlap_chunk.insert(0, w)
                    overlap_size += len(w) + 1

                current_chunk = overlap_chunk
                current_size = sum(len(w) + 1 for w in current_chunk)

            current_chunk.append(word)
            current_size += word_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _generate_chunk_id(
        self, document_id: str, chunk_index: int, content: str
    ) -> str:
        """Generate deterministic chunk ID from document_id, index, and content hash."""
        hash_input = f"{document_id}:{chunk_index}:{content}".encode("utf-8")
        return hashlib.sha256(hash_input).hexdigest()[:32]


class CodeChunker(MarkdownChunker):
    """
    Code-aware chunking strategy (future extensibility).

    For now, delegates to MarkdownChunker with code-specific defaults.
    Future versions will parse AST boundaries for smarter splitting.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        super().__init__(chunk_size=chunk_size, overlap=overlap)
