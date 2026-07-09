"""
Repository Intelligence Layer — Data Models.

All dataclasses used across the repository analysis subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any

from app.analysis.repository.constants import (
    Architecture,
    Layer,
    FileCategory,
    Severity,
)


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


@dataclass
class Dependency:
    """Represents a dependency relationship between two modules."""
    source: str
    target: str
    import_info: Optional[ImportInfo] = None
    is_external: bool = False
    is_stdlib: bool = False


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


@dataclass
class PackageInfo:
    """Info about a Python package (directory with __init__.py)."""
    name: str
    path: str
    modules: List[str] = field(default_factory=list)
    sub_packages: List[str] = field(default_factory=list)


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
