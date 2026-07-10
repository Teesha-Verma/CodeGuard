"""
Repository Intelligence Layer — Hotspot Analyzer.

Identifies high-risk files in a repository by computing a composite
risk score from multiple normalized metrics: import count, caller count,
cyclomatic complexity, file size, class/function counts, and dependency
centrality.
"""

from __future__ import annotations

import ast
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.analysis.repository.constants import (
    HOTSPOT_MIN_IMPORTS,
    HOTSPOT_MIN_LINES,
    HOTSPOT_TOP_N,
)
from app.analysis.repository.models import Hotspot

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Metric weight constants
# ═══════════════════════════════════════════════════════════════════

_W_IMPORT_COUNT: float = 0.20
_W_CALLER_COUNT: float = 0.20
_W_COMPLEXITY: float = 0.15
_W_FILE_SIZE: float = 0.15
_W_CLASS_COUNT: float = 0.10
_W_FUNCTION_COUNT: float = 0.10
_W_CENTRALITY: float = 0.10


def _normalize(value: float, max_value: float) -> float:
    """Normalize *value* to [0, 1] by dividing by *max_value*.

    Returns ``0.0`` when *max_value* is zero or negative.
    """
    if max_value <= 0:
        return 0.0
    return min(value / max_value, 1.0)


def _count_imports(tree: ast.AST) -> int:
    """Count import statements in a parsed AST."""
    count: int = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            count += 1
    return count


def _count_classes(tree: ast.AST) -> int:
    """Count top-level and nested class definitions."""
    count: int = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            count += 1
    return count


def _count_functions(tree: ast.AST) -> int:
    """Count function and async function definitions."""
    count: int = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += 1
    return count


def _build_reverse_graph(
    dependency_graph: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Build a reverse adjacency list: target → list of sources."""
    reverse: Dict[str, List[str]] = defaultdict(list)
    for source, targets in dependency_graph.items():
        for target in targets:
            reverse[target].append(source)
    return dict(reverse)


class HotspotAnalyzer:
    """Compute repository hotspots and rank files by risk.

    A *hotspot* is a file whose combination of structural metrics
    indicates elevated maintenance risk.  Each raw metric is normalized
    against the maximum observed value, then weighted into a composite
    risk score between 0 and 1.
    """

    # ── public API ──────────────────────────────────────────────────

    def analyze(
        self,
        file_sources: Dict[str, str],
        dependency_graph: Optional[Dict[str, List[str]]] = None,
        complexity_data: Optional[Dict[str, int]] = None,
    ) -> List[Hotspot]:
        """Analyse every file and return a list of :class:`Hotspot` objects.

        Parameters
        ----------
        file_sources:
            Mapping of ``file_path → source_code``.
        dependency_graph:
            Optional mapping of ``file_path → [files it depends on]``.
        complexity_data:
            Optional mapping of ``file_path → cyclomatic_complexity``.

        Returns
        -------
        List[Hotspot]
            Sorted by descending ``risk_score``.
        """
        if dependency_graph is None:
            dependency_graph = {}
        if complexity_data is None:
            complexity_data = {}

        reverse_graph: Dict[str, List[str]] = _build_reverse_graph(
            dependency_graph,
        )

        # ── Phase 1: collect raw metrics ────────────────────────────
        raw_hotspots: List[Hotspot] = []

        for file_path, source in file_sources.items():
            hotspot = self._compute_raw_metrics(
                file_path,
                source,
                dependency_graph,
                reverse_graph,
                complexity_data,
            )
            raw_hotspots.append(hotspot)

        if not raw_hotspots:
            return []

        # ── Phase 2: normalize & compute risk scores ────────────────
        self._apply_normalization(raw_hotspots)

        # ── Phase 3: annotate reasons ───────────────────────────────
        for hotspot in raw_hotspots:
            hotspot.reasons = self._collect_reasons(hotspot)

        raw_hotspots.sort(key=lambda h: h.risk_score, reverse=True)
        return raw_hotspots

    # ── ranking helpers ─────────────────────────────────────────────

    @staticmethod
    def top_risky(
        hotspots: List[Hotspot],
        n: int = HOTSPOT_TOP_N,
    ) -> List[Hotspot]:
        """Return the *n* files with the highest composite risk score."""
        return sorted(
            hotspots,
            key=lambda h: h.risk_score,
            reverse=True,
        )[:n]

    @staticmethod
    def top_complex(
        hotspots: List[Hotspot],
        n: int = HOTSPOT_TOP_N,
    ) -> List[Hotspot]:
        """Return the *n* files with the highest cyclomatic complexity."""
        return sorted(
            hotspots,
            key=lambda h: h.cyclomatic_complexity,
            reverse=True,
        )[:n]

    @staticmethod
    def top_coupled(
        hotspots: List[Hotspot],
        n: int = HOTSPOT_TOP_N,
    ) -> List[Hotspot]:
        """Return the *n* files with the highest caller count (fan-in)."""
        return sorted(
            hotspots,
            key=lambda h: h.caller_count,
            reverse=True,
        )[:n]

    @staticmethod
    def top_central(
        hotspots: List[Hotspot],
        n: int = HOTSPOT_TOP_N,
    ) -> List[Hotspot]:
        """Return the *n* files with the highest dependency centrality."""
        return sorted(
            hotspots,
            key=lambda h: h.dependency_centrality,
            reverse=True,
        )[:n]

    # ── internal helpers ────────────────────────────────────────────

    def _compute_raw_metrics(
        self,
        file_path: str,
        source: str,
        dependency_graph: Dict[str, List[str]],
        reverse_graph: Dict[str, List[str]],
        complexity_data: Dict[str, int],
    ) -> Hotspot:
        """Build a :class:`Hotspot` with raw (un-normalized) metrics."""
        lines: int = len(source.splitlines())

        import_count: int = 0
        class_count: int = 0
        function_count: int = 0

        try:
            tree: ast.AST = ast.parse(source, filename=file_path)
            import_count = _count_imports(tree)
            class_count = _count_classes(tree)
            function_count = _count_functions(tree)
        except SyntaxError:
            logger.debug("SyntaxError while parsing %s — skipping AST metrics", file_path)

        fan_out: int = len(dependency_graph.get(file_path, []))
        fan_in: int = len(reverse_graph.get(file_path, []))
        total_connections: int = fan_in + fan_out
        centrality: float = (
            (fan_in * fan_out) / total_connections
            if total_connections > 0
            else 0.0
        )

        return Hotspot(
            file_path=file_path,
            import_count=import_count,
            caller_count=fan_in,
            cyclomatic_complexity=complexity_data.get(file_path, 0),
            file_size_lines=lines,
            class_count=class_count,
            function_count=function_count,
            dependency_centrality=centrality,
        )

    @staticmethod
    def _apply_normalization(hotspots: List[Hotspot]) -> None:
        """Normalize raw metrics across all hotspots and set ``risk_score``."""
        max_import: float = max((h.import_count for h in hotspots), default=0)
        max_caller: float = max((h.caller_count for h in hotspots), default=0)
        max_complexity: float = max(
            (h.cyclomatic_complexity for h in hotspots), default=0
        )
        max_size: float = max((h.file_size_lines for h in hotspots), default=0)
        max_class: float = max((h.class_count for h in hotspots), default=0)
        max_func: float = max((h.function_count for h in hotspots), default=0)
        max_centrality: float = max(
            (h.dependency_centrality for h in hotspots), default=0.0
        )

        for h in hotspots:
            n_import = _normalize(h.import_count, max_import)
            n_caller = _normalize(h.caller_count, max_caller)
            n_complexity = _normalize(h.cyclomatic_complexity, max_complexity)
            n_size = _normalize(h.file_size_lines, max_size)
            n_class = _normalize(h.class_count, max_class)
            n_func = _normalize(h.function_count, max_func)
            n_centrality = _normalize(h.dependency_centrality, max_centrality)

            h.risk_score = (
                _W_IMPORT_COUNT * n_import
                + _W_CALLER_COUNT * n_caller
                + _W_COMPLEXITY * n_complexity
                + _W_FILE_SIZE * n_size
                + _W_CLASS_COUNT * n_class
                + _W_FUNCTION_COUNT * n_func
                + _W_CENTRALITY * n_centrality
            )

    @staticmethod
    def _collect_reasons(hotspot: Hotspot) -> List[str]:
        """Return human-readable risk reasons for a hotspot."""
        reasons: List[str] = []
        if hotspot.import_count >= HOTSPOT_MIN_IMPORTS:
            reasons.append(
                f"High import count ({hotspot.import_count} imports)"
            )
        if hotspot.file_size_lines >= HOTSPOT_MIN_LINES:
            reasons.append(
                f"Large file ({hotspot.file_size_lines} lines)"
            )
        if hotspot.caller_count > 0:
            reasons.append(
                f"Used by {hotspot.caller_count} other module(s)"
            )
        if hotspot.cyclomatic_complexity > 0:
            reasons.append(
                f"Cyclomatic complexity of {hotspot.cyclomatic_complexity}"
            )
        if hotspot.dependency_centrality > 0:
            reasons.append(
                f"Dependency centrality {hotspot.dependency_centrality:.2f}"
            )
        return reasons
