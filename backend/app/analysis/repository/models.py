"""
Repository Intelligence Layer — Data Models.

All dataclasses used across the repository analysis subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Any
from enum import Enum

from app.analysis.repository.constants import (
    Architecture,
    Layer,
    FileCategory,
    Severity,
)


def _serialize_value(val: Any) -> Any:
    """Helper to serialize enums, nested dataclasses, and collections to JSON-compatible types."""
    if isinstance(val, Enum):
        return val.value
    if hasattr(val, "to_dict"):
        return val.to_dict()
    if isinstance(val, list):
        return [_serialize_value(item) for item in val]
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    if isinstance(val, set):
        return [_serialize_value(item) for item in sorted(val)]
    return val


# ═══════════════════════════════════════════════════════════════════
# Import & Dependency Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ImportInfo:
    """Represents a single import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    line: Optional[int] = None
    is_relative: bool = False
    is_from_import: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "names": list(self.names),
            "alias": self.alias,
            "line": self.line,
            "is_relative": self.is_relative,
            "is_from_import": self.is_from_import,
        }


@dataclass
class Dependency:
    """Represents a dependency relationship between two modules."""
    source: str
    target: str
    import_info: Optional[ImportInfo] = None
    is_external: bool = False
    is_stdlib: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "import_info": self.import_info.to_dict() if self.import_info else None,
            "is_external": self.is_external,
            "is_stdlib": self.is_stdlib,
        }


@dataclass
class DependencyMetrics:
    """Metrics for a single module's dependency profile."""
    module: str
    fan_in: int = 0
    fan_out: int = 0
    imports: List[ImportInfo] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    unused_imports: List[ImportInfo] = field(default_factory=list)
    missing_imports: List[str] = field(default_factory=list)
    instability: float = 0.0  # fan_out / (fan_in + fan_out)

    def compute_instability(self) -> None:
        total = self.fan_in + self.fan_out
        self.instability = self.fan_out / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
            "imports": [i.to_dict() for i in self.imports],
            "dependents": list(self.dependents),
            "dependencies": list(self.dependencies),
            "unused_imports": [i.to_dict() for i in self.unused_imports],
            "missing_imports": list(self.missing_imports),
            "instability": self.instability,
        }


# ═══════════════════════════════════════════════════════════════════
# Cycle Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CyclicDependency:
    """Represents a detected circular dependency."""
    cycle: List[str]
    files_involved: List[str] = field(default_factory=list)
    severity: Severity = Severity.MEDIUM
    suggestion: str = ""
    is_package_level: bool = False

    @property
    def length(self) -> int:
        return len(self.cycle)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": list(self.cycle),
            "files_involved": list(self.files_involved),
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "suggestion": self.suggestion,
            "is_package_level": self.is_package_level,
            "length": self.length,
        }


# ═══════════════════════════════════════════════════════════════════
# Architecture Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ArchitectureInfo:
    """Detected architecture pattern with confidence."""
    architecture: Architecture
    confidence: float = 0.0
    detected_layers: List[Layer] = field(default_factory=list)
    detected_directories: List[str] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture": self.architecture.value if hasattr(self.architecture, "value") else str(self.architecture),
            "confidence": self.confidence,
            "detected_layers": [l.value if hasattr(l, "value") else str(l) for l in self.detected_layers],
            "detected_directories": list(self.detected_directories),
            "signals": list(self.signals),
        }


# ═══════════════════════════════════════════════════════════════════
# Hotspot Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Hotspot:
    """A file or module identified as a risk hotspot."""
    file_path: str
    risk_score: float = 0.0
    import_count: int = 0
    caller_count: int = 0
    cyclomatic_complexity: int = 0
    file_size_lines: int = 0
    class_count: int = 0
    function_count: int = 0
    dependency_centrality: float = 0.0
    change_frequency: int = 0  # placeholder
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "risk_score": self.risk_score,
            "import_count": self.import_count,
            "caller_count": self.caller_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "file_size_lines": self.file_size_lines,
            "class_count": self.class_count,
            "function_count": self.function_count,
            "dependency_centrality": self.dependency_centrality,
            "change_frequency": self.change_frequency,
            "reasons": list(self.reasons),
        }


# ═══════════════════════════════════════════════════════════════════
# Layer Violation Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LayerViolation:
    """A detected layer rule violation."""
    violated_rule: str
    source_file: str
    target_file: str
    source_layer: Layer
    target_layer: Layer
    severity: Severity = Severity.MEDIUM
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violated_rule": self.violated_rule,
            "source_file": self.source_file,
            "target_file": self.target_file,
            "source_layer": self.source_layer.value if hasattr(self.source_layer, "value") else str(self.source_layer),
            "target_layer": self.target_layer.value if hasattr(self.target_layer, "value") else str(self.target_layer),
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "reason": self.reason,
        }


# ═══════════════════════════════════════════════════════════════════
# Change Impact Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ChangeImpact:
    """Impact analysis result for a set of changed files."""
    changed_files: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_modules: List[str] = field(default_factory=list)
    indirectly_affected: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    reachability: Dict[str, List[str]] = field(default_factory=dict)
    potential_regression_scope: int = 0
    risk_score: float = 0.0
    risk_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_files": list(self.changed_files),
            "affected_files": list(self.affected_files),
            "affected_modules": list(self.affected_modules),
            "indirectly_affected": list(self.indirectly_affected),
            "affected_functions": list(self.affected_functions),
            "reachability": {k: list(v) for k, v in self.reachability.items()},
            "potential_regression_scope": self.potential_regression_scope,
            "risk_score": self.risk_score,
            "risk_reasons": list(self.risk_reasons),
        }


# ═══════════════════════════════════════════════════════════════════
# File Classification Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FileClassification:
    """Classification of a single file."""
    file_path: str
    category: FileCategory = FileCategory.UNKNOWN
    confidence: float = 0.0
    matched_patterns: List[str] = field(default_factory=list)
    layer: Layer = Layer.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "category": self.category.value if hasattr(self.category, "value") else str(self.category),
            "confidence": self.confidence,
            "matched_patterns": list(self.matched_patterns),
            "layer": self.layer.value if hasattr(self.layer, "value") else str(self.layer),
        }


# ═══════════════════════════════════════════════════════════════════
# Repository Metadata Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DirectoryStats:
    """Statistics for a single directory."""
    path: str
    file_count: int = 0
    python_file_count: int = 0
    total_lines: int = 0
    subdirectory_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "file_count": self.file_count,
            "python_file_count": self.python_file_count,
            "total_lines": self.total_lines,
            "subdirectory_count": self.subdirectory_count,
        }


@dataclass
class ModuleInfo:
    """Info about a Python module."""
    name: str
    file_path: str
    package: Optional[str] = None
    line_count: int = 0
    class_count: int = 0
    function_count: int = 0
    import_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "package": self.package,
            "line_count": self.line_count,
            "class_count": self.class_count,
            "function_count": self.function_count,
            "import_count": self.import_count,
        }


@dataclass
class PackageInfo:
    """Info about a Python package (directory with __init__.py)."""
    name: str
    path: str
    modules: List[str] = field(default_factory=list)
    sub_packages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "modules": list(self.modules),
            "sub_packages": list(self.sub_packages),
        }


@dataclass
class RepositoryMetadata:
    """Overall repository metadata."""
    repository_size_bytes: int = 0
    total_files: int = 0
    total_python_files: int = 0
    total_lines: int = 0
    python_version: Optional[str] = None
    package_manager: Optional[str] = None
    framework: Optional[str] = None
    libraries: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    modules: List[ModuleInfo] = field(default_factory=list)
    packages: List[PackageInfo] = field(default_factory=list)
    directory_stats: List[DirectoryStats] = field(default_factory=list)
    test_coverage: Optional[float] = None  # placeholder

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository_size_bytes": self.repository_size_bytes,
            "total_files": self.total_files,
            "total_python_files": self.total_python_files,
            "total_lines": self.total_lines,
            "python_version": self.python_version,
            "package_manager": self.package_manager,
            "framework": self.framework,
            "libraries": list(self.libraries),
            "entry_points": list(self.entry_points),
            "config_files": list(self.config_files),
            "languages": list(self.languages),
            "modules": [m.to_dict() for m in self.modules],
            "packages": [p.to_dict() for p in self.packages],
            "directory_stats": [d.to_dict() for d in self.directory_stats],
            "test_coverage": self.test_coverage,
        }


# ═══════════════════════════════════════════════════════════════════
# Repository Summary
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RepositorySummary:
    """Complete summary of repository intelligence analysis."""
    metadata: Optional[RepositoryMetadata] = None
    architectures: List[ArchitectureInfo] = field(default_factory=list)
    hotspots: List[Hotspot] = field(default_factory=list)
    cyclic_dependencies: List[CyclicDependency] = field(default_factory=list)
    layer_violations: List[LayerViolation] = field(default_factory=list)
    file_classifications: List[FileClassification] = field(default_factory=list)
    dependency_metrics: List[DependencyMetrics] = field(default_factory=list)
    total_modules: int = 0
    total_packages: int = 0
    total_dependencies: int = 0
    health_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "architectures": [a.to_dict() for a in self.architectures],
            "hotspots": [h.to_dict() for h in self.hotspots],
            "cyclic_dependencies": [c.to_dict() for c in self.cyclic_dependencies],
            "layer_violations": [l.to_dict() for l in self.layer_violations],
            "file_classifications": [f.to_dict() for f in self.file_classifications],
            "dependency_metrics": [d.to_dict() for d in self.dependency_metrics],
            "total_modules": self.total_modules,
            "total_packages": self.total_packages,
            "total_dependencies": self.total_dependencies,
            "health_score": self.health_score,
        }
