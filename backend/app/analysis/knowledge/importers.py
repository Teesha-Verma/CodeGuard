"""
Knowledge importers for loading external documents.

Each importer scans a directory for markdown/text files and
converts them into KnowledgeDocument objects ready for ingestion.

Importers do NOT hardcode documentation or generate artificial knowledge.
They accept external files.
"""

import logging
import os
import uuid
from typing import Any

from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.models import KnowledgeDocument

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst"}


def _extract_title(content: str, fallback: str) -> str:
    """Extract title from first markdown header, or use fallback."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip()
    return fallback


def _scan_directory(directory: str) -> list[str]:
    """Recursively scan directory for supported files."""
    if not os.path.isdir(directory):
        logger.warning("Import directory does not exist: %s", directory)
        return []
    paths: list[str] = []
    for root, _, files in os.walk(directory):
        for fname in sorted(files):
            if os.path.splitext(fname)[1].lower() in _SUPPORTED_EXTENSIONS:
                paths.append(os.path.join(root, fname))
    return paths


def _load_file(file_path: str) -> str | None:
    """Read file content, returning None on failure."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to read '%s': %s", file_path, e)
        return None


def _build_document(
    content: str,
    source: str,
    category: DocumentCategory,
    tags: list[str],
    metadata: dict[str, Any] | None = None,
) -> KnowledgeDocument:
    fallback_title = os.path.splitext(os.path.basename(source))[0]
    return KnowledgeDocument(
        document_id=str(uuid.uuid4()),
        title=_extract_title(content, fallback_title),
        content=content,
        category=category,
        source=source,
        tags=tags,
        metadata=metadata or {},
    )


class OWASPImporter:
    """Imports OWASP documentation from a directory of markdown files."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["owasp", "security"]
                fname = os.path.basename(path).lower()
                # auto-tag OWASP-specific patterns (e.g. a01, a02, ...)
                for i in range(1, 11):
                    if f"a{i:02d}" in fname or f"a{i}" in fname:
                        tags.append(f"owasp-a{i:02d}")
                docs.append(_build_document(content, path, DocumentCategory.OWASP, tags))
        logger.info("OWASPImporter loaded %d documents from '%s'", len(docs), self._directory)
        return docs


class CWEImporter:
    """Imports CWE documentation from a directory of markdown files."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["cwe", "security"]
                fname = os.path.basename(path).lower()
                # auto-tag CWE IDs from filename (e.g. cwe_79.md -> cwe-79)
                import re
                match = re.search(r'cwe[_-]?(\d+)', fname)
                if match:
                    tags.append(f"cwe-{match.group(1)}")
                docs.append(_build_document(content, path, DocumentCategory.CWE, tags))
        logger.info("CWEImporter loaded %d documents from '%s'", len(docs), self._directory)
        return docs


class PythonBestPracticeImporter:
    """Imports Python best practice documentation."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["python", "best-practice"]
                docs.append(_build_document(content, path, DocumentCategory.BEST_PRACTICE, tags))
        logger.info("PythonBestPracticeImporter loaded %d documents", len(docs))
        return docs


class FastAPIBestPracticeImporter:
    """Imports FastAPI best practice documentation."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["fastapi", "best-practice", "python"]
                docs.append(_build_document(content, path, DocumentCategory.BEST_PRACTICE, tags))
        logger.info("FastAPIBestPracticeImporter loaded %d documents", len(docs))
        return docs


class RepositoryRulesImporter:
    """Imports repository-specific rules and conventions."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["repository", "rules"]
                docs.append(_build_document(content, path, DocumentCategory.REPOSITORY, tags))
        logger.info("RepositoryRulesImporter loaded %d documents", len(docs))
        return docs


class SecurityPatternImporter:
    """Imports security vulnerability pattern documentation."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["security", "pattern", "vulnerability"]
                docs.append(_build_document(content, path, DocumentCategory.PATTERN, tags))
        logger.info("SecurityPatternImporter loaded %d documents", len(docs))
        return docs


class HistoricalReviewImporter:
    """Imports historical code review examples."""

    def __init__(self, directory: str):
        self._directory = directory

    def load(self) -> list[KnowledgeDocument]:
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(self._directory):
            content = _load_file(path)
            if content:
                tags = ["historical", "review"]
                docs.append(_build_document(content, path, DocumentCategory.HISTORICAL, tags))
        logger.info("HistoricalReviewImporter loaded %d documents", len(docs))
        return docs
