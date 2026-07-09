"""
Repository Metadata — collects overall repository statistics.

Deterministic metadata extraction from file paths and sources
without re-parsing files unnecessarily.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import PurePosixPath
from typing import Dict, List, Optional, Set

from app.analysis.repository.constants import FRAMEWORK_INDICATORS
from app.analysis.repository.models import (
    RepositoryMetadata,
    ModuleInfo,
    PackageInfo,
    DirectoryStats,
)


class RepositoryMetadataCollector:
    """Collects metadata about a repository from file paths and sources."""

    def __init__(self) -> None:
        self._file_sources: Dict[str, str] = {}
        self._file_paths: List[str] = []

    def collect(
        self,
        file_paths: List[str],
        file_sources: Optional[Dict[str, str]] = None,
    ) -> RepositoryMetadata:
        """Collect repository metadata from file paths and optional sources."""
        self._file_paths = file_paths
        self._file_sources = file_sources or {}

        metadata = RepositoryMetadata()
        metadata.total_files = len(file_paths)
        metadata.total_python_files = len(
            [f for f in file_paths if f.endswith(".py")]
        )
        metadata.languages = self._detect_languages(file_paths)
        metadata.modules = self._collect_modules()
        metadata.packages = self._collect_packages(file_paths)
        metadata.directory_stats = self._collect_directory_stats()
        metadata.config_files = self._find_config_files(file_paths)
        metadata.entry_points = self._find_entry_points(file_paths)
        metadata.package_manager = self._detect_package_manager(file_paths)
        metadata.python_version = self._detect_python_version()

        # Source-dependent analysis
        if self._file_sources:
            metadata.total_lines = sum(
                len(src.splitlines()) for src in self._file_sources.values()
            )
            metadata.repository_size_bytes = sum(
                len(src.encode("utf-8"))
                for src in self._file_sources.values()
            )
            all_imports = self._collect_all_imports()
            metadata.libraries = self._detect_libraries(all_imports)
            metadata.framework = self._detect_framework(all_imports)

        return metadata

    # ── module collection ────────────────────────────────────────

    def _collect_modules(self) -> List[ModuleInfo]:
        modules: List[ModuleInfo] = []
        for fp in self._file_paths:
            if not fp.endswith(".py"):
                continue
            name = self._path_to_module_name(fp)
            pkg = self._path_to_package_name(fp)
            info = ModuleInfo(
                name=name,
                file_path=fp,
                package=pkg,
            )
            source = self._file_sources.get(fp)
            if source:
                info.line_count = len(source.splitlines())
                try:
                    tree = ast.parse(source)
                    info.class_count = sum(
                        1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                    )
                    info.function_count = sum(
                        1
                        for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    )
                    info.import_count = sum(
                        1
                        for n in ast.walk(tree)
                        if isinstance(n, (ast.Import, ast.ImportFrom))
                    )
                except SyntaxError:
                    pass
            modules.append(info)
        return modules

    # ── package collection ───────────────────────────────────────

    def _collect_packages(self, file_paths: List[str]) -> List[PackageInfo]:
        packages: Dict[str, PackageInfo] = {}
        init_dirs: Set[str] = set()

        for fp in file_paths:
            if fp.endswith("__init__.py"):
                dir_path = str(PurePosixPath(fp).parent)
                init_dirs.add(dir_path)

        for dir_path in sorted(init_dirs):
            pkg_name = dir_path.replace("/", ".").replace("\\", ".")
            pkg = PackageInfo(name=pkg_name, path=dir_path)

            for fp in file_paths:
                if fp.startswith(dir_path) and fp.endswith(".py"):
                    rel = fp[len(dir_path):].lstrip("/").lstrip("\\")
                    if "/" not in rel and "\\" not in rel:
                        pkg.modules.append(fp)
                    else:
                        sub_dir = rel.split("/")[0] if "/" in rel else rel.split("\\")[0]
                        sub_path = f"{dir_path}/{sub_dir}"
                        if sub_path in init_dirs and sub_path not in pkg.sub_packages:
                            pkg.sub_packages.append(sub_path)

            packages[dir_path] = pkg

        return list(packages.values())

    # ── directory stats ──────────────────────────────────────────

    def _collect_directory_stats(self) -> List[DirectoryStats]:
        dir_map: Dict[str, DirectoryStats] = {}
        for fp in self._file_paths:
            dir_path = str(PurePosixPath(fp).parent) if "/" in fp or "\\" in fp else "."
            if dir_path not in dir_map:
                dir_map[dir_path] = DirectoryStats(path=dir_path)
            stats = dir_map[dir_path]
            stats.file_count += 1
            if fp.endswith(".py"):
                stats.python_file_count += 1
            source = self._file_sources.get(fp)
            if source:
                stats.total_lines += len(source.splitlines())
        return list(dir_map.values())

    # ── detection helpers ────────────────────────────────────────

    def _detect_languages(self, file_paths: List[str]) -> List[str]:
        extensions: Set[str] = set()
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL",
            ".sh": "Shell",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".json": "JSON",
            ".toml": "TOML",
            ".md": "Markdown",
            ".xml": "XML",
        }
        for fp in file_paths:
            for ext, lang in ext_map.items():
                if fp.endswith(ext):
                    extensions.add(lang)
                    break
        return sorted(extensions)

    def _detect_package_manager(self, file_paths: List[str]) -> Optional[str]:
        basenames = {self._basename(fp) for fp in file_paths}
        if "pyproject.toml" in basenames:
            return "pyproject.toml (PEP 517)"
        if "Pipfile" in basenames:
            return "Pipenv"
        if "requirements.txt" in basenames:
            return "pip"
        if "setup.py" in basenames:
            return "setuptools"
        if "setup.cfg" in basenames:
            return "setuptools"
        if "poetry.lock" in basenames:
            return "Poetry"
        return None

    def _detect_python_version(self) -> Optional[str]:
        return f"{sys.version_info.major}.{sys.version_info.minor}"

    def _find_config_files(self, file_paths: List[str]) -> List[str]:
        config_patterns = {
            "pyproject.toml", "setup.py", "setup.cfg", "tox.ini",
            "Makefile", "Dockerfile", ".env", ".env.example",
            "docker-compose.yml", "docker-compose.yaml",
            "requirements.txt", "requirements-dev.txt",
            "Pipfile", "Pipfile.lock", "poetry.lock",
            ".flake8", ".pylintrc", "mypy.ini", ".pre-commit-config.yaml",
            "pytest.ini", "conftest.py", ".gitignore", ".editorconfig",
        }
        return [fp for fp in file_paths if self._basename(fp) in config_patterns]

    def _find_entry_points(self, file_paths: List[str]) -> List[str]:
        entry_patterns = {"main.py", "app.py", "wsgi.py", "asgi.py", "manage.py", "__main__.py"}
        return [fp for fp in file_paths if self._basename(fp) in entry_patterns]

    def _collect_all_imports(self) -> Set[str]:
        imports: Set[str] = set()
        for source in self._file_sources.values():
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split(".")[0])
            except SyntaxError:
                pass
        return imports

    def _detect_libraries(self, imports: Set[str]) -> List[str]:
        stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()
        external = sorted(imports - stdlib_modules - {"__future__"})
        return external

    def _detect_framework(self, imports: Set[str]) -> Optional[str]:
        for imp_name, framework_name in FRAMEWORK_INDICATORS.items():
            if imp_name in imports:
                return framework_name
        return None

    # ── utilities ────────────────────────────────────────────────

    @staticmethod
    def _path_to_module_name(file_path: str) -> str:
        name = file_path.replace("/", ".").replace("\\", ".")
        if name.endswith(".py"):
            name = name[:-3]
        if name.endswith(".__init__"):
            name = name[:-9]
        return name

    @staticmethod
    def _path_to_package_name(file_path: str) -> Optional[str]:
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None

    @staticmethod
    def _basename(file_path: str) -> str:
        return file_path.replace("\\", "/").split("/")[-1]
