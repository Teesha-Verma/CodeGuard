"""
Repository Query Engine — unified query API for Repository Intelligence.

Orchestrates all analysis modules and provides a single entry point
for querying repository intelligence.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from app.analysis.repository.models import (
    Hotspot,
    CyclicDependency,
    ArchitectureInfo,
    LayerViolation,
    ChangeImpact,
    RepositorySummary,
    RepositoryMetadata,
    FileClassification,
    DependencyMetrics,
)
from app.analysis.repository.dependency_analysis import DependencyAnalyzer
from app.analysis.repository.architecture_detector import ArchitectureDetector
from app.analysis.repository.circular_dependencies import CircularDependencyDetector
from app.analysis.repository.hotspots import HotspotAnalyzer
from app.analysis.repository.layer_violations import LayerViolationDetector
from app.analysis.repository.change_impact import ChangeImpactAnalyzer
from app.analysis.repository.repository_metadata import RepositoryMetadataCollector
from app.analysis.repository.file_classifier import FileClassifier
from app.analysis.repository.repository_graph import RepositoryGraph


class RepositoryQueryEngine:
    """Unified query API for Repository Intelligence Layer.

    Usage::

        engine = RepositoryQueryEngine()
        engine.analyze(file_paths, file_sources)
        hotspots = engine.find_hotspots()
        cycles = engine.find_cycles()
        summary = engine.find_repository_summary()
    """

    def __init__(self) -> None:
        self._file_paths: List[str] = []
        self._file_sources: Dict[str, str] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        self._classifications: List[FileClassification] = []
        self._hotspots: List[Hotspot] = []
        self._cycles: List[CyclicDependency] = []
        self._architectures: List[ArchitectureInfo] = []
        self._violations: List[LayerViolation] = []
        self._metadata: Optional[RepositoryMetadata] = None
        self._dep_metrics: List[DependencyMetrics] = []
        self._repo_graph: Optional[RepositoryGraph] = None
        self._analyzed: bool = False

    # ── main analysis entry point ────────────────────────────────

    def analyze(
        self,
        file_paths: List[str],
        file_sources: Optional[Dict[str, str]] = None,
        complexity_data: Optional[Dict[str, int]] = None,
    ) -> None:
        """Run full repository analysis."""
        self._file_paths = file_paths
        self._file_sources = file_sources or {}

        # 1. Dependency analysis
        dep_analyzer = DependencyAnalyzer()
        if self._file_sources:
            self._dependency_graph = dep_analyzer.build_dependency_graph(
                self._file_sources
            )
        self._dep_metrics = dep_analyzer.dependency_metrics()

        # 2. File classification
        classifier = FileClassifier()
        self._classifications = classifier.classify(
            file_paths, self._file_sources or None
        )

        # 3. Architecture detection
        arch_detector = ArchitectureDetector()
        self._architectures = arch_detector.detect(file_paths)

        # 4. Circular dependencies
        cycle_detector = CircularDependencyDetector()
        self._cycles = cycle_detector.detect(self._dependency_graph)
        self._cycles.extend(
            cycle_detector.detect_package_cycles(self._dependency_graph)
        )

        # 5. Hotspot analysis
        hotspot_analyzer = HotspotAnalyzer()
        if self._file_sources:
            self._hotspots = hotspot_analyzer.analyze(
                self._file_sources,
                self._dependency_graph,
                complexity_data,
            )

        # 6. Layer violations
        violation_detector = LayerViolationDetector()
        self._violations = violation_detector.detect(
            self._classifications, self._dependency_graph
        )

        # 7. Repository metadata
        metadata_collector = RepositoryMetadataCollector()
        self._metadata = metadata_collector.collect(
            file_paths, self._file_sources or None
        )

        # 8. Repository graph
        self._repo_graph = RepositoryGraph()
        self._repo_graph.build_from_analysis(
            file_paths, self._dependency_graph, self._classifications
        )

        self._analyzed = True

    # ── query methods ────────────────────────────────────────────

    def find_hotspots(self, n: int = 20) -> List[Hotspot]:
        """Return the top *n* risk hotspots."""
        return sorted(
            self._hotspots, key=lambda h: h.risk_score, reverse=True
        )[:n]

    def find_dependents(self, file_path: str) -> List[str]:
        """Return all files that depend on *file_path*."""
        dependents: List[str] = []
        for src, targets in self._dependency_graph.items():
            if file_path in targets:
                dependents.append(src)
        return dependents

    def find_dependencies(self, file_path: str) -> List[str]:
        """Return all files that *file_path* depends on."""
        return self._dependency_graph.get(file_path, [])

    def find_cycles(self) -> List[CyclicDependency]:
        """Return all detected cyclic dependencies."""
        return self._cycles

    def find_architecture(self) -> List[ArchitectureInfo]:
        """Return detected architecture patterns with confidence."""
        return sorted(
            self._architectures, key=lambda a: a.confidence, reverse=True
        )

    def find_layer_violations(self) -> List[LayerViolation]:
        """Return all detected layer violations."""
        return self._violations

    def find_change_impact(
        self,
        changed_files: List[str],
        hotspots: Optional[List[Hotspot]] = None,
    ) -> ChangeImpact:
        """Analyze impact of changed files."""
        analyzer = ChangeImpactAnalyzer()
        return analyzer.calculate_impact(
            changed_files,
            self._dependency_graph,
            hotspots or self._hotspots,
        )

    def find_repository_summary(self) -> RepositorySummary:
        """Return a complete repository summary."""
        return RepositorySummary(
            metadata=self._metadata,
            architectures=self._architectures,
            hotspots=self.find_hotspots(),
            cyclic_dependencies=self._cycles,
            layer_violations=self._violations,
            file_classifications=self._classifications,
            dependency_metrics=self._dep_metrics,
            total_modules=len(
                [f for f in self._file_paths if f.endswith(".py")]
            ),
            total_packages=len(self._metadata.packages)
            if self._metadata
            else 0,
            total_dependencies=sum(
                len(deps) for deps in self._dependency_graph.values()
            ),
            health_score=self._compute_health_score(),
        )

    # ── accessors ────────────────────────────────────────────────

    @property
    def dependency_graph(self) -> Dict[str, List[str]]:
        return self._dependency_graph

    @property
    def classifications(self) -> List[FileClassification]:
        return self._classifications

    @property
    def repository_graph(self) -> Optional[RepositoryGraph]:
        return self._repo_graph

    @property
    def metadata(self) -> Optional[RepositoryMetadata]:
        return self._metadata

    # ── health score ─────────────────────────────────────────────

    def _compute_health_score(self) -> float:
        """Compute a 0-1 health score (higher is better)."""
        score = 1.0

        # Penalize for cycles
        if self._cycles:
            score -= min(0.3, len(self._cycles) * 0.05)

        # Penalize for layer violations
        if self._violations:
            score -= min(0.3, len(self._violations) * 0.03)

        # Penalize for high-risk hotspots
        critical_hotspots = [h for h in self._hotspots if h.risk_score > 0.8]
        if critical_hotspots:
            score -= min(0.2, len(critical_hotspots) * 0.04)

        return max(0.0, round(score, 2))
