"""
Repository Intelligence Layer — Dependency Analysis.

Builds module dependency graphs, detects import relationships,
identifies unused / missing / cyclic imports, computes fan-in /
fan-out metrics, and flags heavy dependency chains.
"""

from __future__ import annotations

import ast
import os
import sys
from typing import Dict, List, Optional, Set

from app.analysis.repository.constants import (
    DEPENDENCY_HEAVY_CHAIN_LENGTH,
    DEPENDENCY_MAX_FAN_IN,
    DEPENDENCY_MAX_FAN_OUT,
)
from app.analysis.repository.models import (
    CyclicDependency,
    Dependency,
    DependencyMetrics,
    ImportInfo,
)


# Cache of known stdlib top-level module names (frozen at import time).
_STDLIB_TOP_LEVEL: frozenset[str] = frozenset(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else frozenset()


class DependencyAnalyzer:
    """Analyse inter-module dependencies for a Python repository.

    The analyser receives a mapping of ``{file_path: source_code}`` for
    every Python file in the repository and builds an adjacency-list
    dependency graph.  From this graph it can compute metrics such as
    fan-in / fan-out, detect cycles, unused imports, missing imports,
    and heavy dependency chains.
    """

    # ── construction ────────────────────────────────────────────────

    def __init__(self) -> None:
        self._file_sources: Dict[str, str] = {}
        self._graph: Dict[str, List[str]] = {}
        self._imports_cache: Dict[str, List[ImportInfo]] = {}
        self._dependencies_cache: Dict[str, List[Dependency]] = {}
        # Reverse lookup: normalised module path → file path
        self._module_index: Dict[str, str] = {}

    # ── public API ──────────────────────────────────────────────────

    def build_dependency_graph(
        self,
        file_sources: Dict[str, str],
    ) -> Dict[str, List[str]]:
        """Build the full module dependency graph.

        Parameters
        ----------
        file_sources:
            Mapping of *relative* file paths (e.g. ``"app/models.py"``)
            to their source code.

        Returns
        -------
        Dict[str, List[str]]
            Adjacency list ``{source_file: [imported_file, …]}``.
        """
        self._file_sources = file_sources
        self._graph = {}
        self._imports_cache = {}
        self._dependencies_cache = {}
        self._module_index = self._build_module_index(file_sources)

        for file_path, source in file_sources.items():
            imports = self._extract_imports(source, file_path)
            self._imports_cache[file_path] = imports

            resolved_targets: List[str] = []
            deps: List[Dependency] = []

            for imp in imports:
                is_std = self._is_stdlib(imp.module)
                resolved = self._resolve_import(imp.module)
                is_ext = resolved is None and not is_std

                dep = Dependency(
                    source=file_path,
                    target=resolved or imp.module,
                    import_info=imp,
                    is_external=is_ext,
                    is_stdlib=is_std,
                )
                deps.append(dep)

                if resolved is not None:
                    resolved_targets.append(resolved)

            self._dependencies_cache[file_path] = deps
            self._graph[file_path] = resolved_targets

        # Ensure every file appears as a key even if it imports nothing.
        for file_path in file_sources:
            self._graph.setdefault(file_path, [])

        return self._graph

    def get_imports(self, file_path: str) -> List[ImportInfo]:
        """Return the parsed imports for *file_path*."""
        return list(self._imports_cache.get(file_path, []))

    def get_dependents(self, file_path: str) -> List[str]:
        """Return files that import *file_path* (fan-in list)."""
        dependents: List[str] = []
        for source, targets in self._graph.items():
            if file_path in targets:
                dependents.append(source)
        return dependents

    def find_cycles(self) -> List[CyclicDependency]:
        """Detect cyclic import chains using the current graph.

        Delegates to :class:`CircularDependencyDetector` internally so
        that the algorithm is encapsulated in one place.
        """
        from app.analysis.repository.circular_dependencies import (
            CircularDependencyDetector,
        )

        detector = CircularDependencyDetector()
        return detector.detect(self._graph)

    def dependency_metrics(self) -> List[DependencyMetrics]:
        """Compute :class:`DependencyMetrics` for every module."""
        metrics: List[DependencyMetrics] = []

        for file_path, source in self._file_sources.items():
            imports = self._imports_cache.get(file_path, [])
            dependents = self.get_dependents(file_path)
            dependencies = self._graph.get(file_path, [])

            unused = self._find_unused_in_file(source, imports)
            missing = self._find_missing_imports(file_path)

            fan_in = len(dependents)
            fan_out = len(dependencies)

            dm = DependencyMetrics(
                module=file_path,
                fan_in=fan_in,
                fan_out=fan_out,
                imports=imports,
                dependents=dependents,
                dependencies=list(dependencies),
                unused_imports=unused,
                missing_imports=missing,
            )
            dm.compute_instability()
            metrics.append(dm)

        return metrics

    # ── heavy chain detection ───────────────────────────────────────

    def find_heavy_chains(self) -> List[List[str]]:
        """Return dependency chains longer than *DEPENDENCY_HEAVY_CHAIN_LENGTH*.

        Uses iterative DFS from every node to enumerate simple paths.
        """
        heavy: List[List[str]] = []

        for start in self._graph:
            # Iterative DFS with path tracking
            stack: List[tuple[str, List[str]]] = [(start, [start])]
            while stack:
                node, path = stack.pop()
                if len(path) > DEPENDENCY_HEAVY_CHAIN_LENGTH:
                    heavy.append(list(path))
                    continue  # prune — don't extend further
                for neighbour in self._graph.get(node, []):
                    if neighbour not in path:  # avoid cycles
                        stack.append((neighbour, path + [neighbour]))

        return heavy

    # ── internal helpers ────────────────────────────────────────────

    def _extract_imports(
        self,
        source: str,
        file_path: str,
    ) -> List[ImportInfo]:
        """Parse *source* with :mod:`ast` and return all imports."""
        imports: List[ImportInfo] = []

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            names=[alias.name.rsplit(".", 1)[-1]],
                            alias=alias.asname,
                            line=node.lineno,
                            is_relative=False,
                            is_from_import=False,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                is_relative = (node.level or 0) > 0

                # Resolve relative imports to an absolute dotted path.
                if is_relative and module_name:
                    resolved_module = self._resolve_relative_import(
                        file_path, module_name, node.level or 0,
                    )
                elif is_relative:
                    resolved_module = self._resolve_relative_import(
                        file_path, "", node.level or 0,
                    )
                else:
                    resolved_module = module_name

                names: List[str] = [
                    a.name for a in (node.names or [])
                ]
                alias: Optional[str] = None
                if node.names and len(node.names) == 1:
                    alias = node.names[0].asname

                imports.append(
                    ImportInfo(
                        module=resolved_module,
                        names=names,
                        alias=alias,
                        line=node.lineno,
                        is_relative=is_relative,
                        is_from_import=True,
                    )
                )

        return imports

    def _resolve_import(self, import_name: str) -> Optional[str]:
        """Map a dotted import name to a file path in the repo.

        Returns ``None`` when the import cannot be resolved to a known
        file (i.e. it is external or stdlib).
        """
        # Try direct module match
        if import_name in self._module_index:
            return self._module_index[import_name]

        # Try successive parent packages
        parts = import_name.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            if candidate in self._module_index:
                return self._module_index[candidate]

        return None

    def _resolve_relative_import(
        self,
        file_path: str,
        module_name: str,
        level: int,
    ) -> str:
        """Resolve a relative import to an absolute dotted path."""
        # Determine package of the importing file.
        parts = file_path.replace("\\", "/").replace("/", ".").split(".")
        # Strip the ``.py`` extension if present.
        if parts and parts[-1] == "py":
            parts = parts[:-1]
        # Remove the file's own module name (the last component).
        if parts:
            parts = parts[:-1]
        # Walk up *level - 1* directories (level 1 = same package).
        for _ in range(level - 1):
            if parts:
                parts = parts[:-1]

        base = ".".join(parts)
        if module_name:
            return f"{base}.{module_name}" if base else module_name
        return base

    def _find_unused_in_file(
        self,
        source: str,
        imports: List[ImportInfo],
    ) -> List[ImportInfo]:
        """Return imports whose bound names never appear in the AST body."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        # Gather all Name / Attribute identifiers used outside import
        # statements.
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)

        unused: List[ImportInfo] = []
        for imp in imports:
            # Determine the names this import binds into the namespace.
            bound: List[str] = []
            if imp.alias:
                bound.append(imp.alias)
            elif imp.is_from_import:
                bound.extend(imp.names)
            else:
                # ``import foo.bar`` → the bound name is ``foo``
                bound.append(imp.module.split(".")[0])

            # If *none* of the bound names is referenced, flag as unused.
            if bound and not any(name in used_names for name in bound):
                unused.append(imp)

        return unused

    def _find_missing_imports(self, file_path: str) -> List[str]:
        """Return import names that could not be resolved to repo files
        and are *not* stdlib or known-external packages.

        A missing import typically means the import target is absent
        from the analysed source tree.
        """
        missing: List[str] = []
        for dep in self._dependencies_cache.get(file_path, []):
            if dep.is_stdlib or dep.is_external:
                continue
            if self._resolve_import(dep.import_info.module if dep.import_info else dep.target) is None:
                missing.append(dep.target)
        return missing

    # ── utilities ───────────────────────────────────────────────────

    @staticmethod
    def _build_module_index(
        file_sources: Dict[str, str],
    ) -> Dict[str, str]:
        """Create a reverse mapping from dotted module paths to file paths."""
        index: Dict[str, str] = {}
        for file_path in file_sources:
            normalised = (
                file_path
                .replace("\\", "/")
                .replace("/", ".")
            )
            # Strip ``.py`` extension.
            if normalised.endswith(".py"):
                normalised = normalised[:-3]
            # Strip leading dots.
            normalised = normalised.lstrip(".")
            index[normalised] = file_path

            # Also add the ``__init__`` form as the package itself.
            if normalised.endswith(".__init__"):
                package = normalised[: -len(".__init__")]
                index[package] = file_path

        return index

    @staticmethod
    def _is_stdlib(module_name: str) -> bool:
        """Return ``True`` when *module_name* belongs to the stdlib."""
        top = module_name.split(".")[0]
        if _STDLIB_TOP_LEVEL:
            return top in _STDLIB_TOP_LEVEL
        # Fallback for older Python versions: check if the module lives
        # under the known stdlib prefix.
        try:
            import importlib.util

            spec = importlib.util.find_spec(top)
            if spec is None:
                return False
            origin = spec.origin or ""
            return "site-packages" not in origin and "dist-packages" not in origin
        except (ModuleNotFoundError, ValueError):
            return False
