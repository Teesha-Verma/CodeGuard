"""Intelligent semantic chunking.

Chunks knowledge documents while preserving:
- Section boundaries
- Semantic meaning
- Metadata attachment
- References back to original document

Supports configurable chunk sizes and overlap.
"""
from __future__ import annotations

import uuid

from app.analysis.RAG.config.settings import ChunkingConfig
from app.analysis.RAG.models.documents import KnowledgeDocument, KnowledgeChunk
from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("chunker")


def _build_metadata_header(doc: KnowledgeDocument) -> str:
    """Build a metadata header string to prepend to chunks."""
    meta = doc.metadata
    parts = []
    title = meta.embedding_title or meta.title
    if title:
        parts.append(f"Title: {title}")
    if meta.category:
        parts.append(f"Category: {meta.category}")
    if meta.subcategory:
        parts.append(f"Subcategory: {meta.subcategory}")
    if meta.tags:
        parts.append(f"Tags: {', '.join(meta.tags[:5])}")
    return "\n".join(parts)


def _split_text_with_overlap(
    text: str,
    max_size: int,
    overlap: int,
) -> list[str]:
    """Split text into chunks respecting paragraph boundaries with overlap."""
    if len(text) <= max_size:
        return [text]

    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if not current:
            current = para
        elif len(current) + len(para) + 2 <= max_size:
            current += "\n\n" + para
        else:
            chunks.append(current)
            # Apply overlap: take last `overlap` chars from previous chunk
            if overlap > 0 and len(current) > overlap:
                overlap_text = current[-overlap:]
                # Find clean break point
                break_idx = overlap_text.find("\n")
                if break_idx > 0:
                    overlap_text = overlap_text[break_idx + 1:]
                current = overlap_text + "\n\n" + para
            else:
                current = para

    if current.strip():
        chunks.append(current)

    # Handle paragraphs that are individually too large
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_size:
            final.append(chunk)
        else:
            # Hard split by sentences/chars
            for i in range(0, len(chunk), max_size - overlap):
                final.append(chunk[i : i + max_size])

    return final


def chunk_document(
    doc: KnowledgeDocument,
    config: ChunkingConfig | None = None,
) -> list[KnowledgeChunk]:
    """Chunk a knowledge document into semantic chunks.
    
    Strategy:
    1. If preserve_sections is True, chunk by section first.
    2. Each section is split if it exceeds max_chunk_size.
    3. Metadata header is prepended to each chunk.
    4. Each chunk maintains a reference to its source document.
    """
    config = config or ChunkingConfig()
    chunks: list[KnowledgeChunk] = []

    metadata_header = ""
    if config.include_metadata_header:
        metadata_header = _build_metadata_header(doc)

    # Reserve space for metadata header
    available_size = config.max_chunk_size
    if metadata_header:
        available_size -= len(metadata_header) + 4  # 4 for "\n\n---\n"
    available_size = max(available_size, config.min_chunk_size)

    if config.preserve_sections and doc.sections:
        # Chunk by section
        for section_title, section_content in doc.sections.items():
            if not section_content.strip():
                continue

            text_parts = _split_text_with_overlap(
                section_content,
                available_size,
                config.chunk_overlap,
            )
            for part in text_parts:
                content = f"# {section_title}\n\n{part}"
                if metadata_header:
                    content = f"{metadata_header}\n\n---\n{content}"
                chunks.append(
                    KnowledgeChunk(
                        document_id=doc.document_id,
                        content=content,
                        section_title=section_title,
                        source_path=doc.source_path,
                        metadata=doc.metadata,
                    )
                )
    else:
        # Chunk the full body
        text_parts = _split_text_with_overlap(
            doc.body,
            available_size,
            config.chunk_overlap,
        )
        for part in text_parts:
            content = part
            if metadata_header:
                content = f"{metadata_header}\n\n---\n{content}"
            chunks.append(
                KnowledgeChunk(
                    document_id=doc.document_id,
                    content=content,
                    source_path=doc.source_path,
                    metadata=doc.metadata,
                )
            )

    # Filter out chunks that are too small
    chunks = [c for c in chunks if len(c.content.strip()) >= config.min_chunk_size]

    # Set indices
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.total_chunks = len(chunks)

    logger.debug(
        "Document '%s' → %d chunks",
        doc.document_id, len(chunks),
    )
    return chunks


def chunk_documents(
    documents: list[KnowledgeDocument],
    config: ChunkingConfig | None = None,
) -> list[KnowledgeChunk]:
    """Chunk multiple documents."""
    config = config or ChunkingConfig()
    all_chunks: list[KnowledgeChunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, config))
    logger.info("Chunked %d documents → %d total chunks", len(documents), len(all_chunks))
    return all_chunks
