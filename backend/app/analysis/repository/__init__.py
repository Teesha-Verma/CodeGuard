"""
CodeGuard V2 — Repository Intelligence Layer.

Standalone subsystem for whole-repository analysis including
dependency analysis, architecture detection, circular dependency
detection, hotspot analysis, layer violations, change impact,
repository metadata, file classification, and repository graph.

Sub-modules:
    constants          Enums, thresholds, pattern registries
    models             All dataclass models
    dependency_analysis  Module/package dependency graph & metrics
    architecture_detector  Architecture pattern detection
    circular_dependencies  Tarjan SCC-based cycle detection
    hotspots           Composite risk hotspot analysis
    layer_violations   Architecture layering rule enforcement
    change_impact      Changed file impact analysis
    repository_metadata  Repo-wide metadata collection
    file_classifier    Semantic file tagging
    repository_graph   Graph Foundation-based repo graph
    query_engine       Unified query API
"""

# Constants & Enums
from app.analysis.repository.constants import (
    Architecture,
    Layer,
    FileCategory,
    Severity,
    RepoNodeKind,
    RepoEdgeKind,
)

# Models
from app.analysis.repository.models import (
    ImportInfo,
    Dependency,
    DependencyMetrics,
    CyclicDependency,
    ArchitectureInfo,
    Hotspot,
    LayerViolation,
    ChangeImpact,
    FileClassification,
    DirectoryStats,
    ModuleInfo,
    PackageInfo,
    RepositoryMetadata,
    RepositorySummary,
)

# Analysis Modules
from app.analysis.repository.dependency_analysis import DependencyAnalyzer
from app.analysis.repository.architecture_detector import ArchitectureDetector
from app.analysis.repository.circular_dependencies import CircularDependencyDetector
from app.analysis.repository.hotspots import HotspotAnalyzer
from app.analysis.repository.layer_violations import LayerViolationDetector
from app.analysis.repository.change_impact import ChangeImpactAnalyzer
from app.analysis.repository.repository_metadata import RepositoryMetadataCollector
from app.analysis.repository.file_classifier import FileClassifier
from app.analysis.repository.repository_graph import (
    RepositoryGraph,
    RepoGraphNode,
    RepoGraphEdge,
)
from app.analysis.repository.query_engine import RepositoryQueryEngine

__all__ = [
    # Constants
    "Architecture",
    "Layer",
    "FileCategory",
    "Severity",
    "RepoNodeKind",
    "RepoEdgeKind",
    # Models
    "ImportInfo",
    "Dependency",
    "DependencyMetrics",
    "CyclicDependency",
    "ArchitectureInfo",
    "Hotspot",
    "LayerViolation",
    "ChangeImpact",
    "FileClassification",
    "DirectoryStats",
    "ModuleInfo",
    "PackageInfo",
    "RepositoryMetadata",
    "RepositorySummary",
    # Analysis Modules
    "DependencyAnalyzer",
    "ArchitectureDetector",
    "CircularDependencyDetector",
    "HotspotAnalyzer",
    "LayerViolationDetector",
    "ChangeImpactAnalyzer",
    "RepositoryMetadataCollector",
    "FileClassifier",
    "RepositoryGraph",
    "RepoGraphNode",
    "RepoGraphEdge",
    "RepositoryQueryEngine",
]
