"""
CodeGuard V2 — PR Supporting Context Provider.

Enforces strict separation between PRIMARY ANALYSIS SCOPE and SUPPORTING CONTEXT SCOPE.
- PRIMARY ANALYSIS SCOPE: Files directly changed by the PR.
- SUPPORTING CONTEXT SCOPE: Minimal supporting files, functions, and symbols
  genuinely required to understand the changed files (e.g., imported modules,
  called functions, inherited base classes).

Guarantees:
- Does NOT scan or parse the entire repository.
- Supporting files are NEVER treated as primary review targets.
- Supporting files do NOT produce reportable PR review findings.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from app.diff.diff_parser import DiffFile
from app.analysis.repository.query_engine import RepositoryQueryEngine


@dataclass
class SupportingSymbol:
    """A specific function, class, or constant definition retrieved as supporting context."""
    symbol_name: str
    file_path: str
    kind: str  # "function", "class", "variable"
    signature: str
    line_number: int
    docstring: Optional[str] = None
    summary: str = ""


@dataclass
class PRContextBundle:
    """Separated container for PR analysis scope vs secondary supporting context."""
    primary_files: List[str]
    primary_sources: Dict[str, str]
    supporting_files: List[str]
    supporting_sources: Dict[str, str]
    supporting_symbols: Dict[str, SupportingSymbol] = field(default_factory=dict)
    repo_intelligence: Dict[str, Any] = field(default_factory=dict)

    @property
    def combined_sources_cache(self) -> Dict[str, str]:
        """Scoped sources cache containing ONLY primary files and supporting context files."""
        return {**self.supporting_sources, **self.primary_sources}


class PRSupportingContextProvider:
    """
    Analyzes PR-scoped files to discover and load ONLY the targeted supporting context
    needed to understand the changes.
    """

    def __init__(
        self,
        repo_dir: str = "",
        max_supporting_files: int = 15,
        pr_changed_files: Optional[List[str]] = None,
        repo_path: Optional[str] = None
    ):
        self.repo_dir = repo_path or repo_dir
        self.max_supporting_files = max_supporting_files
        self.pr_changed_files = pr_changed_files or []

    @classmethod
    def normalize_path(cls, p: str) -> str:
        """Normalize repository-relative path with forward slashes."""
        cleaned = p.strip().replace("\\", "/")
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        return cleaned.lstrip("/")

    def filter_primary_files(self, candidate_files: List[str], pr_changed_files: Optional[List[str]] = None) -> List[str]:
        """Filter candidate paths to only those matching exact normalized PR changed files."""
        targets = pr_changed_files if pr_changed_files is not None else self.pr_changed_files
        norm_pr_set = {self.normalize_path(f) for f in targets if f}
        return [f for f in candidate_files if self.normalize_path(f) in norm_pr_set]

    def build_supporting_context(self) -> PRContextBundle:
        """Convenience method to build supporting context from configured pr_changed_files."""
        diff_files = [
            DiffFile(file_path=p, is_new=False, added_lines=[])
            for p in self.pr_changed_files
        ]
        return self.resolve_context(diff_files)

    def resolve_context(self, primary_diff_files: List[DiffFile]) -> PRContextBundle:
        """
        Builds the PRContextBundle by loading primary files and resolving only the
        specific supporting files/symbols needed to understand the PR.
        """
        primary_files: List[str] = []
        primary_sources: Dict[str, str] = {}
        primary_trees: Dict[str, ast.AST] = {}

        # 1. Load primary PR files
        for df in primary_diff_files:
            norm_p = self.normalize_path(df.file_path)
            if df.is_deleted or not norm_p.endswith(".py"):
                continue
            full_p = os.path.join(self.repo_dir, norm_p)
            if os.path.isfile(full_p):
                try:
                    with open(full_p, "r", encoding="utf-8") as f:
                        code = f.read()
                    primary_files.append(norm_p)
                    primary_sources[norm_p] = code
                    try:
                        primary_trees[norm_p] = ast.parse(code)
                    except Exception:
                        pass
                except Exception:
                    pass

        # 2. Extract needed imports and references from primary files
        needed_modules: Set[str] = set()
        for norm_p, tree in primary_trees.items():
            file_dir = os.path.dirname(norm_p)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        needed_modules.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    level = node.level or 0
                    if level > 0:
                        # Relative import: resolve relative to file_dir
                        rel_dir_parts = file_dir.split("/") if file_dir else []
                        up_steps = level - 1
                        if up_steps <= len(rel_dir_parts):
                            base_parts = rel_dir_parts[:len(rel_dir_parts) - up_steps] if up_steps > 0 else rel_dir_parts
                            resolved_mod = ".".join(base_parts + ([mod] if mod else []))
                            if resolved_mod:
                                needed_modules.add(resolved_mod)
                    elif mod:
                        needed_modules.add(mod)

        # 3. Locate and load ONLY the matching supporting files on disk
        primary_set = set(primary_files)
        supporting_files: List[str] = []
        supporting_sources: Dict[str, str] = {}

        for mod in sorted(needed_modules):
            if len(supporting_files) >= self.max_supporting_files:
                break
            candidate_paths = self._module_to_candidate_paths(mod)
            for cand in candidate_paths:
                norm_cand = self.normalize_path(cand)
                if norm_cand in primary_set or norm_cand in supporting_sources:
                    continue
                full_cand = os.path.join(self.repo_dir, norm_cand)
                if os.path.isfile(full_cand):
                    try:
                        with open(full_cand, "r", encoding="utf-8") as sf:
                            code = sf.read()
                        supporting_files.append(norm_cand)
                        supporting_sources[norm_cand] = code
                        break
                    except Exception:
                        pass

        # 4. Extract supporting symbols (function signatures, classes) from supporting files
        supporting_symbols: Dict[str, SupportingSymbol] = {}
        for s_path, s_code in supporting_sources.items():
            try:
                s_tree = ast.parse(s_code)
                for node in ast.walk(s_tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in node.args.args]
                        sig = f"{node.name}({', '.join(args)})"
                        supporting_symbols[node.name] = SupportingSymbol(
                            symbol_name=node.name,
                            file_path=s_path,
                            kind="function",
                            signature=sig,
                            line_number=node.lineno,
                            docstring=ast.get_docstring(node),
                            summary=f"Defined in supporting file {s_path}:{node.lineno}"
                        )
                    elif isinstance(node, ast.ClassDef):
                        bases = [getattr(b, "id", getattr(b, "attr", "")) for b in node.bases]
                        sig = f"class {node.name}({', '.join(b for b in bases if b)})"
                        supporting_symbols[node.name] = SupportingSymbol(
                            symbol_name=node.name,
                            file_path=s_path,
                            kind="class",
                            signature=sig,
                            line_number=node.lineno,
                            docstring=ast.get_docstring(node),
                            summary=f"Defined in supporting file {s_path}:{node.lineno}"
                        )
            except Exception:
                pass

        # 5. Compute scoped repository intelligence over ONLY primary + supporting files
        scoped_sources = {**supporting_sources, **primary_sources}
        repo_intel: Dict[str, Any] = {}
        if scoped_sources:
            try:
                query_engine = RepositoryQueryEngine(sources=scoped_sources, changed_files=primary_files)
                repo_intel = {
                    "architecture": [a.to_dict() for a in query_engine.find_architecture()],
                    "hotspots": [h.to_dict() for h in query_engine.find_hotspots(top_n=5)],
                    "change_impact": query_engine.find_change_impact().to_dict() if query_engine.find_change_impact() else {},
                    "supporting_files_count": len(supporting_files),
                }
            except Exception:
                repo_intel = {"supporting_files_count": len(supporting_files)}

        return PRContextBundle(
            primary_files=primary_files,
            primary_sources=primary_sources,
            supporting_files=supporting_files,
            supporting_sources=supporting_sources,
            supporting_symbols=supporting_symbols,
            repo_intelligence=repo_intel,
        )

    def _module_to_candidate_paths(self, module_name: str) -> List[str]:
        """Converts dotted module name to candidate repository-relative file paths."""
        parts = module_name.split(".")
        path_base = "/".join(parts)
        candidates = [
            f"{path_base}.py",
            f"{path_base}/__init__.py",
        ]
        # Also check with common prefix variations (e.g., app/..., src/...)
        for prefix in ("app", "src", "backend", "backend/app"):
            candidates.append(f"{prefix}/{path_base}.py")
            candidates.append(f"{prefix}/{path_base}/__init__.py")
        return candidates
