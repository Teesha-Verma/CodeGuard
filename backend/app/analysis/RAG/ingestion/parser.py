"""Markdown and YAML frontmatter parser.

Parses knowledge documents:
1. Extracts YAML frontmatter between --- delimiters.
2. Parses the Markdown body.
3. Extracts sections by # headers.
4. Computes content hash for change detection.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

import yaml

from app.analysis.RAG.models.documents import DocumentMetadata, KnowledgeDocument
from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("parser")

_FRONTMATTER_RE = re.compile(
    r"\A\s*---\s*\n(.*?)\n---\s*\n",
    re.DOTALL,
)

_SECTION_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_frontmatter(raw_content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from raw markdown.
    
    Returns:
        (frontmatter_dict, body_text). If no frontmatter found, returns ({}, full_text).
    """
    match = _FRONTMATTER_RE.match(raw_content)
    if not match:
        return {}, raw_content.strip()

    yaml_text = match.group(1)
    body = raw_content[match.end():].strip()

    try:
        frontmatter = yaml.safe_load(yaml_text)
        if not isinstance(frontmatter, dict):
            logger.warning("Frontmatter parsed as non-dict type: %s", type(frontmatter))
            return {}, raw_content.strip()
    except yaml.YAMLError as e:
        logger.warning("Failed to parse YAML frontmatter: %s", e)
        return {}, raw_content.strip()

    return frontmatter, body


def extract_sections(body: str) -> dict[str, str]:
    """Extract top-level sections (# Header) from markdown body.
    
    Returns dict mapping section title -> section content.
    """
    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(body))

    if not matches:
        return sections

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections[title] = content

    return sections


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of raw file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_document(file_path: str) -> KnowledgeDocument | None:
    """Parse a single markdown knowledge document.
    
    Returns:
        KnowledgeDocument or None if parsing fails.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Failed to read '%s': %s", file_path, e)
        return None

    if not raw.strip():
        logger.warning("Empty file: '%s'", file_path)
        return None

    frontmatter, body = parse_frontmatter(raw)
    sections = extract_sections(body)
    content_hash = compute_content_hash(raw)

    if frontmatter:
        metadata = DocumentMetadata.from_frontmatter(frontmatter)
    else:
        # Fallback: derive minimal metadata from filename
        import os
        base = os.path.splitext(os.path.basename(file_path))[0]
        metadata = DocumentMetadata(
            document_id=base,
            title=base.replace("_", " ").title(),
            category="unknown",
        )

    return KnowledgeDocument(
        metadata=metadata,
        body=body,
        sections=sections,
        source_path=file_path,
        content_hash=content_hash,
    )
