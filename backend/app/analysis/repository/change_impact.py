"""
Repository Intelligence Layer — Change Impact Analyzer.

Given a set of changed files, determines which other files and modules
are transitively affected, then computes a risk score reflecting the
blast radius and whether any hotspots fall within the impact zone.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set

from app.analysis.repository.constants import (
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
)
from app.analysis.repository.models import ChangeImpact, Hotspot

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Thresholds for risk adjustments
# ═══════════════════════════════════════════════════════════════════

_HOTSPOT_RISK_MULTIPLIER: float = 1.5
_LARGE_BLAST_RADIUS_THRESHOLD: int = 20
_LARGE_BLAST_RADIUS_BONUS: float = 0.2
_MAX_RISK: float = 1.0


def _build_reverse_graph(
    dependency_graph: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Build a reverse adjacency list: target → list of sources.

    In the forward graph ``A → [B, C]`` means *A depends on B and C*.
    The reverse graph ``B → [A]`` means *A is a dependent of B* — i.e.
    changing B may impact A.
    """
    reverse: Dict[str, List[str]] = defaultdict(list)
    for source, targets in dependency_graph.items():
        for target in targets:
            reverse[target].append(source)
    return dict(reverse)


def _extract_module(file_path: str) -> str:
    """Derive a module path from a file path.

    A simple heuristic: strip ``.py``, replace separators with dots,
    and drop a trailing ``.__init__`` if present.
    """
    module = file_path.replace("\\", "/")
    if module.endswith(".py"):
        module = module[:-3]
    module = module.replace("/", ".")
    if module.endswith(".__init__"):
        module = module[: -len(".__init__")]
    return module


class ChangeImpactAnalyzer:
    """Analyse the impact of file changes on a repository.

    The analyzer walks the reverse dependency graph to determine which
    files are transitively affected, then scores the overall risk.
    """

    # ── public API ──────────────────────────────────────────────────

    def calculate_impact(
        self,
        changed_files: List[str],
        dependency_graph: Dict[str, List[str]],
        hotspots: Optional[List[Hotspot]] = None,
    ) -> ChangeImpact:
        """Calculate the full change-impact for *changed_files*.

        Parameters
        ----------
        changed_files:
            File paths that have been modified.
        dependency_graph:
            Mapping of ``file → [files it depends on]``.
        hotspots:
            Optional precomputed hotspot list used to amplify risk
            when a hotspot is within the blast radius.

        Returns
        -------
        ChangeImpact
            Populated impact model with affected files, modules,
            reachability map, and risk score.
        """
        if hotspots is None:
            hotspots = []

        # Collect all transitively affected files.
        all_affected: Set[str] = set()
        reachability: Dict[str, List[str]] = {}

        for changed in changed_files:
            dependents: List[str] = self.transitive_dependents(
                changed, dependency_graph,
            )
            reachability[changed] = dependents
            all_affected.update(dependents)

        # Remove the changed files themselves from the affected set.
        direct_affected: List[str] = sorted(all_affected - set(changed_files))

        # Indirectly affected: depth ≥ 2 — dependents that are NOT
        # direct importers.
        reverse_graph: Dict[str, List[str]] = _build_reverse_graph(
            dependency_graph,
        )
        direct_dependents: Set[str] = set()
        for changed in changed_files:
            direct_dependents.update(reverse_graph.get(changed, []))
        indirectly_affected: List[str] = sorted(
            all_affected - direct_dependents - set(changed_files),
        )

        # Derive affected modules.
        aff_modules: List[str] = self.affected_modules(
            changed_files, dependency_graph,
        )

        # Compute risk score.
        total_files: int = max(len(dependency_graph), 1)
        risk: float = len(direct_affected) / total_files

        hotspot_paths: Set[str] = {h.file_path for h in hotspots}
        hotspot_hit: bool = bool(
            (set(direct_affected) | set(changed_files)) & hotspot_paths,
        )
        risk_reasons: List[str] = []

        if hotspot_hit:
            risk *= _HOTSPOT_RISK_MULTIPLIER
            risk_reasons.append(
                "Affected file(s) include known hotspot(s)"
            )

        if len(direct_affected) > _LARGE_BLAST_RADIUS_THRESHOLD:
            risk += _LARGE_BLAST_RADIUS_BONUS
            risk_reasons.append(
                f"Large blast radius: {len(direct_affected)} affected files"
            )

        risk = min(risk, _MAX_RISK)

        if risk >= RISK_THRESHOLD_HIGH:
            risk_reasons.append("Risk score exceeds HIGH threshold")
        elif risk >= RISK_THRESHOLD_MEDIUM:
            risk_reasons.append("Risk score exceeds MEDIUM threshold")

        return ChangeImpact(
            changed_files=list(changed_files),
            affected_files=direct_affected,
            affected_modules=aff_modules,
            indirectly_affected=indirectly_affected,
            affected_functions=[],  # populated via affected_functions()
            reachability=reachability,
            potential_regression_scope=len(direct_affected),
            risk_score=round(risk, 4),
            risk_reasons=risk_reasons,
        )

    def affected_functions(
        self,
        changed_files: List[str],
        call_graph: Optional[Any] = None,
    ) -> List[str]:
        """Return functions potentially affected by the changed files.

        Parameters
        ----------
        changed_files:
            File paths that have been modified.
        call_graph:
            An optional :class:`CallGraph` (or similar) object that
            exposes a ``get_callers(file_path)`` method.  If ``None``,
            an empty list is returned.

        Returns
        -------
        List[str]
            Qualified function names that may be impacted.
        """
        if call_graph is None:
            return []

        affected: Set[str] = set()
        for file_path in changed_files:
            get_callers = getattr(call_graph, "get_callers", None)
            if callable(get_callers):
                callers: List[str] = get_callers(file_path)
                affected.update(callers)
        return sorted(affected)

    def affected_modules(
        self,
        changed_files: List[str],
        dependency_graph: Dict[str, List[str]],
    ) -> List[str]:
        """Return the unique module names affected by the change.

        Each transitively affected file is mapped to a module name,
        then deduplicated.
        """
        all_affected: Set[str] = set()
        for changed in changed_files:
            dependents = self.transitive_dependents(
                changed, dependency_graph,
            )
            all_affected.update(dependents)

        modules: Set[str] = set()
        for file_path in all_affected:
            modules.add(_extract_module(file_path))

        return sorted(modules)

    def transitive_dependents(
        self,
        file_path: str,
        dependency_graph: Dict[str, List[str]],
    ) -> List[str]:
        """BFS through the reverse dependency graph.

        Returns all files that directly **or** indirectly depend on
        *file_path*.

        Parameters
        ----------
        file_path:
            The file whose dependents are sought.
        dependency_graph:
            Mapping of ``file → [files it depends on]``.

        Returns
        -------
        List[str]
            Sorted list of transitively dependent file paths
            (excluding *file_path* itself).
        """
        reverse_graph: Dict[str, List[str]] = _build_reverse_graph(
            dependency_graph,
        )

        visited: Set[str] = set()
        queue: deque[str] = deque()

        # Seed the BFS with the direct dependents of `file_path`.
        for dep in reverse_graph.get(file_path, []):
            if dep not in visited:
                visited.add(dep)
                queue.append(dep)

        while queue:
            current: str = queue.popleft()
            for dependent in reverse_graph.get(current, []):
                if dependent not in visited:
                    visited.add(dependent)
                    queue.append(dependent)

        # Exclude the starting file itself if it appeared via a cycle.
        visited.discard(file_path)
        return sorted(visited)
