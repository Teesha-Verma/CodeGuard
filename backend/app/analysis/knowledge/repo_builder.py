"""
Repository Knowledge Builder.

Automatically converts repository documentation into KnowledgeDocuments:
- README files
- docs/ directory
- CONTRIBUTING guides
- Architecture documents
- Repository summaries
"""

import logging
import os
import uuid
from typing import Any

from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.models import KnowledgeDocument

logger = logging.getLogger(__name__)

# Files to look for in repo root
_ROOT_DOC_PATTERNS = [
    "README.md", "README.rst", "README.txt", "README",
    "CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt", "CONTRIBUTING",
    "ARCHITECTURE.md", "ARCHITECTURE.rst", "ARCHITECTURE.txt",
    "DESIGN.md", "DESIGN.rst",
    "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
]

_DOC_DIRS = ["docs", "doc", "documentation"]

_SUPPORTED_EXTENSIONS = {".md", ".rst", ".txt"}


class RepositoryKnowledgeBuilder:
    """
    Builds KnowledgeDocuments from a repository's documentation structure.
    
    Scans:
    - Root-level documentation files (README, CONTRIBUTING, etc.)
    - Documentation directories (docs/, doc/, documentation/)
    """

    def __init__(self, repo_path: str, repository_url: str = ""):
        self._repo_path = repo_path
        self._repository_url = repository_url

    def build(self) -> list[KnowledgeDocument]:
        """Scan repository and build KnowledgeDocuments from documentation."""
        if not os.path.isdir(self._repo_path):
            logger.warning("Repository path does not exist: %s", self._repo_path)
            return []

        documents: list[KnowledgeDocument] = []

        # 1. Root-level documentation files
        for pattern in _ROOT_DOC_PATTERNS:
            full_path = os.path.join(self._repo_path, pattern)
            if os.path.isfile(full_path):
                doc = self._load_file(full_path, self._classify_root_file(pattern))
                if doc:
                    documents.append(doc)

        # 2. Documentation directories
        for dir_name in _DOC_DIRS:
            docs_dir = os.path.join(self._repo_path, dir_name)
            if os.path.isdir(docs_dir):
                docs_from_dir = self._scan_docs_directory(docs_dir)
                documents.extend(docs_from_dir)

        logger.info(
            "RepositoryKnowledgeBuilder built %d documents from '%s'",
            len(documents), self._repo_path,
        )
        return documents

    def _scan_docs_directory(self, docs_dir: str) -> list[KnowledgeDocument]:
        """Recursively scan a documentation directory."""
        documents: list[KnowledgeDocument] = []
        for root, _, files in os.walk(docs_dir):
            for fname in sorted(files):
                if os.path.splitext(fname)[1].lower() in _SUPPORTED_EXTENSIONS:
                    full_path = os.path.join(root, fname)
                    doc = self._load_file(full_path, self._classify_doc_file(fname))
                    if doc:
                        documents.append(doc)
        return documents

    def _load_file(self, file_path: str, tags: list[str]) -> KnowledgeDocument | None:
        """Load a single file into a KnowledgeDocument."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                return None

            title = self._extract_title(content, os.path.basename(file_path))
            rel_path = os.path.relpath(file_path, self._repo_path)

            return KnowledgeDocument(
                document_id=str(uuid.uuid4()),
                title=title,
                content=content,
                category=DocumentCategory.REPOSITORY,
                source=rel_path,
                tags=tags,
                metadata={
                    "repository_url": self._repository_url,
                    "file_path": rel_path,
                    "content_hash": self._compute_hash(content),
                },
            )
        except Exception as e:
            logger.error("Failed to load repo doc '%s': %s", file_path, e)
            return None

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.lstrip("# ").strip()
        return os.path.splitext(fallback)[0]

    @staticmethod
    def _compute_hash(content: str) -> str:
        import hashlib
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _classify_root_file(filename: str) -> list[str]:
        """Generate tags for root-level documentation files."""
        tags = ["repository", "documentation"]
        lower = filename.lower()
        if "readme" in lower:
            tags.append("readme")
        elif "contributing" in lower:
            tags.append("contributing")
        elif "architecture" in lower or "design" in lower:
            tags.append("architecture")
        elif "changelog" in lower:
            tags.append("changelog")
        elif "security" in lower:
            tags.extend(["security", "security-policy"])
        return tags

    @staticmethod
    def _classify_doc_file(filename: str) -> list[str]:
        """Generate tags for files in documentation directories."""
        tags = ["repository", "documentation"]
        lower = filename.lower()
        if "api" in lower:
            tags.append("api")
        elif "setup" in lower or "install" in lower:
            tags.append("setup")
        elif "config" in lower:
            tags.append("configuration")
        elif "deploy" in lower:
            tags.append("deployment")
        elif "test" in lower:
            tags.append("testing")
        return tags
