"""
Repository Intelligence Layer — Circular Dependency Detection.

Implements Tarjan's Strongly-Connected-Components algorithm to detect
direct, multi-file, and package-level circular import chains.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from app.analysis.repository.constants import Severity
from app.analysis.repository.models import CyclicDependency


class CircularDependencyDetector:
    """Detect circular dependencies in a module dependency graph.

    The detector operates on a plain adjacency-list representation
    ``{module: [dependency, …]}`` and uses *Tarjan's algorithm* to find
    all strongly-connected components (SCCs).  Each SCC with more than
    one node represents a circular dependency chain.
    """

    # ── public API ──────────────────────────────────────────────────

    def detect(
        self,
        dependency_graph: Dict[str, List[str]],
    ) -> List[CyclicDependency]:
        """Return all circular dependency chains in *dependency_graph*.

        Parameters
        ----------
        dependency_graph:
            Adjacency list ``{source_file: [imported_file, …]}``.

        Returns
        -------
        List[CyclicDependency]
            One entry per detected cycle, annotated with severity and a
            human-readable suggestion.
        """
        sccs = self._tarjan_scc(dependency_graph)
        results: List[CyclicDependency] = []

        for scc in sccs:
            if len(scc) < 2:
                continue

            # Extract the minimal cycle path within the SCC.
            cycle_path = self._extract_cycle_path(scc, dependency_graph)
            severity = self._severity_for_length(len(cycle_path))
            suggestion = self._suggestion_for_cycle(cycle_path)

            results.append(
                CyclicDependency(
                    cycle=cycle_path,
                    files_involved=sorted(scc),
                    severity=severity,
                    suggestion=suggestion,
                    is_package_level=False,
                )
            )

        return results

    def detect_package_cycles(
        self,
        dependency_graph: Dict[str, List[str]],
    ) -> List[CyclicDependency]:
        """Detect circular dependencies at the *package* level.

        Modules are collapsed to their top-level package (the first
        path component) before cycle detection runs.

        Parameters
        ----------
        dependency_graph:
            Module-level adjacency list.

        Returns
        -------
        List[CyclicDependency]
            Package-level cycles (always severity ``HIGH``).
        """
        pkg_graph = self._build_package_graph(dependency_graph)
        sccs = self._tarjan_scc(pkg_graph)
        results: List[CyclicDependency] = []

        for scc in sccs:
            if len(scc) < 2:
                continue

            cycle_path = self._extract_cycle_path(scc, pkg_graph)
            suggestion = self._suggestion_for_package_cycle(cycle_path)

            # Collect all original files that belong to the packages in
            # this SCC so the caller knows what to look at.
            files_involved: List[str] = sorted(
                {
                    module
                    for module in dependency_graph
                    if self._package_of(module) in scc
                }
            )

            results.append(
                CyclicDependency(
                    cycle=cycle_path,
                    files_involved=files_involved,
                    severity=Severity.HIGH,
                    suggestion=suggestion,
                    is_package_level=True,
                )
            )

        return results

    # ── Tarjan's SCC ────────────────────────────────────────────────

    def _tarjan_scc(
        self,
        graph: Dict[str, List[str]],
    ) -> List[List[str]]:
        """Iterative Tarjan's algorithm returning all SCCs.

        The implementation avoids recursion so that deeply nested graphs
        do not hit Python's default recursion limit.
        """
        index_counter: List[int] = [0]
        node_index: Dict[str, int] = {}
        node_lowlink: Dict[str, int] = {}
        on_stack: Set[str] = set()
        stack: List[str] = []
        result: List[List[str]] = []

        # Collect every reachable node (graph may reference nodes that
        # are not keys in the dict).
        all_nodes: Set[str] = set(graph.keys())
        for targets in graph.values():
            all_nodes.update(targets)

        for node in sorted(all_nodes):
            if node in node_index:
                continue
            self._tarjan_strongconnect_iterative(
                node,
                graph,
                index_counter,
                node_index,
                node_lowlink,
                on_stack,
                stack,
                result,
            )

        return result

    def _tarjan_strongconnect_iterative(
        self,
        start: str,
        graph: Dict[str, List[str]],
        index_counter: List[int],
        node_index: Dict[str, int],
        node_lowlink: Dict[str, int],
        on_stack: Set[str],
        stack: List[str],
        result: List[List[str]],
    ) -> None:
        """Process one connected component starting at *start*."""
        # Each frame: (node, neighbour_iterator, phase)
        # phase 0 → initialise; phase 1 → resume after child returned
        work_stack: List[tuple[str, int, Optional[str]]] = [
            (start, 0, None),
        ]
        # We keep a per-node iterator state via a dict.
        neighbour_iters: Dict[str, int] = {}

        while work_stack:
            node, phase, returning_child = work_stack[-1]

            if phase == 0:
                # First visit ─ initialise the node.
                node_index[node] = index_counter[0]
                node_lowlink[node] = index_counter[0]
                index_counter[0] += 1
                stack.append(node)
                on_stack.add(node)
                neighbour_iters[node] = 0
                # Move to iteration phase.
                work_stack[-1] = (node, 1, None)
                continue

            # phase == 1 — iterate over neighbours.
            if returning_child is not None:
                node_lowlink[node] = min(
                    node_lowlink[node],
                    node_lowlink[returning_child],
                )

            neighbours = graph.get(node, [])
            idx = neighbour_iters[node]

            advanced = False
            while idx < len(neighbours):
                w = neighbours[idx]
                idx += 1
                neighbour_iters[node] = idx

                if w not in node_index:
                    # Tree edge — recurse.
                    work_stack.append((w, 0, None))
                    # When *w* returns we will resume with returning_child=w.
                    work_stack[-2] = (node, 1, w)
                    advanced = True
                    break
                elif w in on_stack:
                    node_lowlink[node] = min(
                        node_lowlink[node],
                        node_index[w],
                    )

            if advanced:
                continue

            # All neighbours explored — check if *node* is an SCC root.
            if node_lowlink[node] == node_index[node]:
                scc: List[str] = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == node:
                        break
                result.append(scc)

            work_stack.pop()

    # ── cycle path extraction ───────────────────────────────────────

    @staticmethod
    def _extract_cycle_path(
        scc: List[str],
        graph: Dict[str, List[str]],
    ) -> List[str]:
        """Extract one representative cycle path from an SCC.

        Performs a DFS inside the SCC sub-graph starting from the
        lexicographically smallest node, returning the first cycle
        found (closed path back to the start).
        """
        scc_set = set(scc)
        start = min(scc)

        # DFS stack: (current_node, path)
        dfs_stack: List[tuple[str, List[str]]] = [(start, [start])]
        visited: Set[str] = set()

        while dfs_stack:
            current, path = dfs_stack.pop()

            for neighbour in graph.get(current, []):
                if neighbour not in scc_set:
                    continue
                if neighbour == start and len(path) > 1:
                    # Found a cycle — close it.
                    return path + [start]
                if neighbour not in visited:
                    visited.add(neighbour)
                    dfs_stack.append((neighbour, path + [neighbour]))

        # Fallback: return the SCC nodes with the start repeated.
        return sorted(scc) + [min(scc)]

    # ── package graph ───────────────────────────────────────────────

    @staticmethod
    def _build_package_graph(
        dependency_graph: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        """Collapse a module-level graph into a package-level graph."""
        pkg_graph: Dict[str, Set[str]] = {}

        for module, deps in dependency_graph.items():
            src_pkg = CircularDependencyDetector._package_of(module)
            if src_pkg not in pkg_graph:
                pkg_graph[src_pkg] = set()
            for dep in deps:
                tgt_pkg = CircularDependencyDetector._package_of(dep)
                if tgt_pkg != src_pkg:
                    pkg_graph[src_pkg].add(tgt_pkg)

        return {pkg: sorted(deps) for pkg, deps in pkg_graph.items()}

    @staticmethod
    def _package_of(module_path: str) -> str:
        """Return the top-level package for a file path or dotted name."""
        normalised = module_path.replace("\\", "/")
        parts = normalised.split("/")
        return parts[0] if parts else module_path

    # ── severity / suggestion ───────────────────────────────────────

    @staticmethod
    def _severity_for_length(length: int) -> Severity:
        """Map cycle length to a severity level.

        * Direct cycle (length 2): ``HIGH``
        * Multi-file cycle (3-4): ``MEDIUM``
        * Long cycle (5+): ``LOW``
        """
        if length <= 2:
            return Severity.HIGH
        if length <= 4:
            return Severity.MEDIUM
        return Severity.LOW

    @staticmethod
    def _suggestion_for_cycle(cycle: List[str]) -> str:
        """Generate an actionable suggestion for a module-level cycle."""
        if len(cycle) <= 3:
            # Direct cycle (A -> B -> A)
            a = cycle[0]
            b = cycle[1] if len(cycle) > 1 else cycle[0]
            return (
                f"Consider introducing an interface/abstraction to "
                f"break the cycle between {a} and {b}"
            )

        modules = " -> ".join(cycle)
        return (
            f"Refactor the dependency chain ({modules}) by "
            f"extracting shared types into a common module or using "
            f"dependency inversion to eliminate the cycle"
        )

    @staticmethod
    def _suggestion_for_package_cycle(cycle: List[str]) -> str:
        """Generate a suggestion for a package-level cycle."""
        if len(cycle) <= 3:
            a = cycle[0]
            b = cycle[1] if len(cycle) > 1 else cycle[0]
            return (
                f"Consider introducing an interface/abstraction to "
                f"break the cycle between packages {a} and {b}"
            )

        packages = " -> ".join(cycle)
        return (
            f"Restructure package boundaries ({packages}) to "
            f"enforce a unidirectional dependency flow"
        )
