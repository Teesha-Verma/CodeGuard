"""Knowledge file discovery.

Recursively discovers all Markdown files in the knowledge directory,
skipping metadata files (README.md, CONTRIBUTING.md, etc.) at the root level.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("discovery")

_ROOT_SKIP_FILES = {
    "README.md", "CONTRIBUTING.md", "DOCUMENT_SCHEMA.md",
    "CATEGORY_MAPPING.md", "KNOWLEDGE_INDEX.md", "SOURCES.md",
    "VERSION_HISTORY.md",
}


def discover_knowledge_files(
    knowledge_dir: str,
    extensions: list[str] | None = None,
) -> list[str]:
    """Recursively discover all knowledge markdown files.
    
    Args:
        knowledge_dir: Root directory of the knowledge base.
        extensions: File extensions to include (default: [".md"]).
        
    Returns:
        Sorted list of absolute file paths.
    """
    extensions = extensions or [".md"]
    if not os.path.isdir(knowledge_dir):
        logger.warning("Knowledge directory does not exist: %s", knowledge_dir)
        return []

    root_path = Path(knowledge_dir).resolve()
    found: list[str] = []

    for dirpath, _, filenames in os.walk(root_path):
        current = Path(dirpath)
        for fname in sorted(filenames):
            # Check extension
            if not any(fname.lower().endswith(ext) for ext in extensions):
                continue
            # Skip root-level metadata files
            if current == root_path and fname in _ROOT_SKIP_FILES:
                continue
            found.append(str(current / fname))

    logger.info("Discovered %d knowledge files in '%s'", len(found), knowledge_dir)
    return sorted(found)
