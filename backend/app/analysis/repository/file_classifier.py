"""
Repository Intelligence Layer — File Classifier.

Classifies Python source files into semantic categories
(controller, service, model, …) using filename patterns,
directory patterns, and lightweight content analysis.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Set

from app.analysis.repository.constants import (
    FileCategory,
    Layer,
    FILE_NAME_PATTERNS,
    DIRECTORY_PATTERNS,
)
from app.analysis.repository.models import FileClassification


# ═══════════════════════════════════════════════════════════════════
# Confidence scores
# ═══════════════════════════════════════════════════════════════════

_CONF_FILENAME: float = 0.90
_CONF_DIRECTORY: float = 0.80
_CONF_CONTENT: float = 0.60
_CONF_BOOST: float = 0.05

# ═══════════════════════════════════════════════════════════════════
# Content-based class-name suffixes → FileCategory
# ═══════════════════════════════════════════════════════════════════

_CONTENT_SIGNALS: Dict[str, FileCategory] = {
    "Controller": FileCategory.CONTROLLER,
    "Handler": FileCategory.CONTROLLER,
    "View": FileCategory.CONTROLLER,
    "Service": FileCategory.SERVICE,
    "UseCase": FileCategory.SERVICE,
    "Interactor": FileCategory.SERVICE,
    "Model": FileCategory.MODEL,
    "Entity": FileCategory.MODEL,
    "Schema": FileCategory.SCHEMA,
    "Serializer": FileCategory.SCHEMA,
    "Repository": FileCategory.REPOSITORY,
    "Repo": FileCategory.REPOSITORY,
    "DAO": FileCategory.REPOSITORY,
    "Middleware": FileCategory.MIDDLEWARE,
    "Decorator": FileCategory.DECORATOR,
    "Migration": FileCategory.MIGRATION,
    "Config": FileCategory.CONFIGURATION,
    "Settings": FileCategory.CONFIGURATION,
    "Command": FileCategory.CLI,
}

# ═══════════════════════════════════════════════════════════════════
# Category → Layer mapping
# ═══════════════════════════════════════════════════════════════════

_CATEGORY_TO_LAYER: Dict[FileCategory, Layer] = {
    FileCategory.CONTROLLER: Layer.CONTROLLER,
    FileCategory.SERVICE: Layer.SERVICE,
    FileCategory.MODEL: Layer.MODEL,
    FileCategory.REPOSITORY: Layer.REPOSITORY,
    FileCategory.SCHEMA: Layer.SCHEMA,
    FileCategory.DTO: Layer.DTO,
    FileCategory.UTILITY: Layer.UTILITY,
    FileCategory.CONFIGURATION: Layer.CONFIGURATION,
    FileCategory.MIGRATION: Layer.MIGRATION,
    FileCategory.GENERATED: Layer.GENERATED,
    FileCategory.TEST: Layer.TEST,
    FileCategory.CLI: Layer.CLI,
    FileCategory.API: Layer.API,
    FileCategory.MIDDLEWARE: Layer.MIDDLEWARE,
    FileCategory.DECORATOR: Layer.DECORATOR,
    FileCategory.SECURITY: Layer.SECURITY,
    FileCategory.DATABASE: Layer.DATABASE,
    FileCategory.INFRASTRUCTURE: Layer.INFRASTRUCTURE,
    FileCategory.TEMPLATE: Layer.TEMPLATE,
    FileCategory.UNKNOWN: Layer.UNKNOWN,
}


class FileClassifier:
    """Classify Python files into semantic :class:`FileCategory` values.

    The classifier applies a priority chain:

    1. **Test detection** — filenames starting with ``test_`` or ending
       with ``_test.py``, or files inside a ``tests/`` directory.
    2. **Filename pattern** — the file stem is checked against
       :const:`FILE_NAME_PATTERNS` (confidence 0.90).
    3. **Directory pattern** — each parent directory is checked against
       :const:`DIRECTORY_PATTERNS` (confidence 0.80).
    4. **Content analysis** — when *source* is available, class-name
       suffixes (e.g. ``*Controller``, ``*Service``) are matched
       (confidence 0.60).

    When multiple signals agree on the same category the confidence is
    boosted by 0.05 (capped at 1.0).
    """

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def classify(
        self,
        file_paths: List[str],
        file_sources: Optional[Dict[str, str]] = None,
    ) -> List[FileClassification]:
        """Classify a batch of files.

        Parameters
        ----------
        file_paths:
            Iterable of file-path strings (relative or absolute).
        file_sources:
            Optional mapping of ``file_path → source_code``.  When
            provided, content-based analysis is applied for the
            corresponding files.

        Returns
        -------
        list[FileClassification]
            One :class:`FileClassification` per input path (order
            preserved).
        """
        sources = file_sources or {}
        return [
            self.classify_file(fp, source=sources.get(fp))
            for fp in file_paths
        ]

    def classify_file(
        self,
        file_path: str,
        source: Optional[str] = None,
    ) -> FileClassification:
        """Classify a single file.

        Parameters
        ----------
        file_path:
            Path to the Python file (relative or absolute).
        source:
            Optional source code of the file for content-based
            analysis.

        Returns
        -------
        FileClassification
        """
        normalised = file_path.replace("\\", "/")
        parts = [p for p in normalised.split("/") if p]
        filename = parts[-1] if parts else ""
        stem = filename.rsplit(".", 1)[0].lower() if filename else ""
        dir_parts = [p.lower() for p in parts[:-1]] if len(parts) > 1 else []

        # Collect (category, confidence, pattern_label) hits.
        hits: List[_Hit] = []

        # 1. Test detection  ─────────────────────────────────────
        if self._is_test_file(stem, filename, dir_parts):
            hits.append(_Hit(FileCategory.TEST, _CONF_FILENAME, "test_detection"))

        # 2. Filename pattern matching  ──────────────────────────
        filename_hit = self._match_filename(stem)
        if filename_hit is not None:
            hits.append(filename_hit)

        # 3. Directory pattern matching  ─────────────────────────
        directory_hit = self._match_directory(dir_parts)
        if directory_hit is not None:
            hits.append(directory_hit)

        # 4. Content-based analysis  ─────────────────────────────
        if source is not None:
            content_hit = self._match_content(source)
            if content_hit is not None:
                hits.append(content_hit)

        # ── Resolve final category and confidence ───────────────
        if not hits:
            return FileClassification(
                file_path=file_path,
                category=FileCategory.UNKNOWN,
                confidence=0.0,
                matched_patterns=[],
                layer=Layer.UNKNOWN,
            )

        category, confidence, patterns = self._resolve_hits(hits)

        return FileClassification(
            file_path=file_path,
            category=category,
            confidence=confidence,
            matched_patterns=patterns,
            layer=self.get_layer(category),
        )

    @staticmethod
    def get_layer(category: FileCategory) -> Layer:
        """Map a :class:`FileCategory` to its architectural :class:`Layer`.

        Parameters
        ----------
        category:
            The file category to look up.

        Returns
        -------
        Layer
        """
        return _CATEGORY_TO_LAYER.get(category, Layer.UNKNOWN)

    # ──────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_test_file(
        stem: str,
        filename: str,
        dir_parts: List[str],
    ) -> bool:
        """Return *True* if the file looks like a test file."""
        if stem.startswith("test_"):
            return True
        if filename.lower().endswith("_test.py"):
            return True
        if stem == "conftest":
            return True
        if any(d in ("tests", "test", "spec") for d in dir_parts):
            return True
        return False

    @staticmethod
    def _match_filename(stem: str) -> Optional[_Hit]:
        """Match the file stem against :const:`FILE_NAME_PATTERNS`."""
        # Exact match.
        if stem in FILE_NAME_PATTERNS:
            return _Hit(
                FILE_NAME_PATTERNS[stem],
                _CONF_FILENAME,
                f"filename:{stem}",
            )

        # Suffix / prefix matching: e.g. "user_controller" contains
        # the token "controller".
        for pattern, category in FILE_NAME_PATTERNS.items():
            if pattern in stem:
                return _Hit(
                    category,
                    _CONF_FILENAME,
                    f"filename:{pattern}",
                )

        return None

    @staticmethod
    def _match_directory(dir_parts: List[str]) -> Optional[_Hit]:
        """Match parent directories against :const:`DIRECTORY_PATTERNS`."""
        # Walk from deepest to shallowest so the nearest parent wins.
        for d in reversed(dir_parts):
            if d in DIRECTORY_PATTERNS:
                return _Hit(
                    DIRECTORY_PATTERNS[d],
                    _CONF_DIRECTORY,
                    f"directory:{d}",
                )
        return None

    @staticmethod
    def _match_content(source: str) -> Optional[_Hit]:
        """Lightweight content scan for class-name suffixes."""
        for suffix, category in _CONTENT_SIGNALS.items():
            # Look for "class SomethingSuffix" style declarations.
            marker = f"class "
            for line in source.splitlines():
                stripped = line.strip()
                if not stripped.startswith(marker):
                    continue
                # Extract class name (up to '(' or ':').
                after_class = stripped[len(marker):]
                class_name = ""
                for ch in after_class:
                    if ch in ("(", ":", " "):
                        break
                    class_name += ch

                if class_name.endswith(suffix) and class_name != suffix:
                    return _Hit(
                        category,
                        _CONF_CONTENT,
                        f"content:class *{suffix}",
                    )
        return None

    @staticmethod
    def _resolve_hits(hits: List[_Hit]) -> tuple[FileCategory, float, List[str]]:
        """Pick the best category from collected hits, apply boosting."""
        # Sort by descending confidence.
        hits.sort(key=lambda h: h.confidence, reverse=True)
        best = hits[0]

        # Count how many distinct signals agree with the best category.
        agreeing = [h for h in hits if h.category == best.category]
        confidence = best.confidence
        if len(agreeing) > 1:
            confidence = min(confidence + _CONF_BOOST, 1.0)

        patterns = [h.label for h in hits]
        return best.category, round(confidence, 4), patterns


# ═══════════════════════════════════════════════════════════════════
# Internal helper dataclass (module-private)
# ═══════════════════════════════════════════════════════════════════

class _Hit:
    """Lightweight container for a classification hit."""
    __slots__ = ("category", "confidence", "label")

    def __init__(
        self,
        category: FileCategory,
        confidence: float,
        label: str,
    ) -> None:
        self.category = category
        self.confidence = confidence
        self.label = label
