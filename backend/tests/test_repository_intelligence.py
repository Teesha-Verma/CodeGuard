"""
Tests for the Repository Intelligence Layer.

Covers all 10 analysis modules, models, constants, and query engine.
"""

import pytest
from typing import Dict, List

from app.analysis.repository.constants import (
    Architecture,
    Layer,
    FileCategory,
    Severity,
    RepoNodeKind,
    RepoEdgeKind,
    LAYER_RULES,
    HOTSPOT_TOP_N,
)
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


# ═══════════════════════════════════════════════════════════════════
# Shared fixtures
# ═══════════════════════════════════════════════════════════════════

SAMPLE_SOURCES: Dict[str, str] = {
    "app/controllers/user_controller.py": (
        "from app.services.user_service import UserService\n"
        "from app.models.user import User\n"
        "\n"
        "class UserController:\n"
        "    def __init__(self):\n"
        "        self.service = UserService()\n"
        "\n"
        "    def get_user(self, user_id):\n"
        "        return self.service.get(user_id)\n"
    ),
    "app/services/user_service.py": (
        "from app.models.user import User\n"
        "from app.repositories.user_repo import UserRepository\n"
        "\n"
        "class UserService:\n"
        "    def __init__(self):\n"
        "        self.repo = UserRepository()\n"
        "\n"
        "    def get(self, user_id):\n"
        "        return self.repo.find(user_id)\n"
    ),
    "app/models/user.py": (
        "class User:\n"
        "    def __init__(self, id, name):\n"
        "        self.id = id\n"
        "        self.name = name\n"
    ),
    "app/repositories/user_repo.py": (
        "from app.models.user import User\n"
        "\n"
        "class UserRepository:\n"
        "    def find(self, user_id):\n"
        "        return User(user_id, 'test')\n"
    ),
    "app/utils/helpers.py": (
        "def format_name(name):\n"
        "    return name.strip().title()\n"
    ),
    "tests/test_user.py": (
        "from app.models.user import User\n"
        "\n"
        "def test_user_creation():\n"
        "    u = User(1, 'Test')\n"
        "    assert u.name == 'Test'\n"
    ),
    "app/__init__.py": "",
    "app/models/__init__.py": "",
    "app/services/__init__.py": "",
    "app/controllers/__init__.py": "",
    "app/repositories/__init__.py": "",
}


# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

class TestConstants:
    def test_architecture_enum(self):
        assert Architecture.MVC.value == "mvc"
        assert Architecture.CLEAN.value == "clean_architecture"

    def test_layer_enum(self):
        assert Layer.CONTROLLER.value == "controller"
        assert Layer.SERVICE.value == "service"

    def test_file_category_enum(self):
        assert FileCategory.TEST.value == "test"
        assert FileCategory.MODEL.value == "model"

    def test_severity_enum(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"

    def test_repo_node_kind_enum(self):
        assert RepoNodeKind.FILE.value == "repo_file"
        assert RepoNodeKind.PACKAGE.value == "repo_package"

    def test_layer_rules_exist(self):
        assert Layer.CONTROLLER in LAYER_RULES
        assert Layer.MODEL in LAYER_RULES


# ═══════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════

class TestModels:
    def test_import_info(self):
        info = ImportInfo(module="os", names=["path"], line=1)
        assert info.module == "os"
        assert not info.is_relative

    def test_dependency(self):
        dep = Dependency(source="a.py", target="b.py")
        assert dep.source == "a.py"
        assert not dep.is_external

    def test_dependency_metrics_instability(self):
        m = DependencyMetrics(module="test", fan_in=5, fan_out=10)
        m.compute_instability()
        assert abs(m.instability - (10 / 15)) < 0.001

    def test_dependency_metrics_instability_zero(self):
        m = DependencyMetrics(module="test", fan_in=0, fan_out=0)
        m.compute_instability()
        assert m.instability == 0.0

    def test_cyclic_dependency_length(self):
        c = CyclicDependency(cycle=["a", "b", "a"])
        assert c.length == 3

    def test_hotspot_defaults(self):
        h = Hotspot(file_path="test.py")
        assert h.risk_score == 0.0
        assert h.reasons == []

    def test_change_impact_defaults(self):
        ci = ChangeImpact()
        assert ci.risk_score == 0.0
        assert ci.changed_files == []

    def test_repository_summary(self):
        rs = RepositorySummary(total_modules=5, health_score=0.85)
        assert rs.total_modules == 5
        assert rs.health_score == 0.85

    def test_file_classification(self):
        fc = FileClassification(
            file_path="test.py",
            category=FileCategory.TEST,
            confidence=0.9,
        )
        assert fc.category == FileCategory.TEST


# ═══════════════════════════════════════════════════════════════════
# Dependency Analysis
# ═══════════════════════════════════════════════════════════════════

class TestDependencyAnalysis:
    def test_build_dependency_graph(self):
        analyzer = DependencyAnalyzer()
        graph = analyzer.build_dependency_graph(SAMPLE_SOURCES)
        assert isinstance(graph, dict)
        assert len(graph) > 0

    def test_get_imports(self):
        analyzer = DependencyAnalyzer()
        analyzer.build_dependency_graph(SAMPLE_SOURCES)
        imports = analyzer.get_imports("app/controllers/user_controller.py")
        assert isinstance(imports, list)

    def test_get_dependents(self):
        analyzer = DependencyAnalyzer()
        analyzer.build_dependency_graph(SAMPLE_SOURCES)
        deps = analyzer.get_dependents("app/models/user.py")
        assert isinstance(deps, list)

    def test_dependency_metrics(self):
        analyzer = DependencyAnalyzer()
        analyzer.build_dependency_graph(SAMPLE_SOURCES)
        metrics = analyzer.dependency_metrics()
        assert isinstance(metrics, list)
        assert all(isinstance(m, DependencyMetrics) for m in metrics)

    def test_empty_sources(self):
        analyzer = DependencyAnalyzer()
        graph = analyzer.build_dependency_graph({})
        assert graph == {}

    def test_syntax_error_handled(self):
        analyzer = DependencyAnalyzer()
        graph = analyzer.build_dependency_graph(
            {"bad.py": "def broken(\n"}
        )
        assert isinstance(graph, dict)


# ═══════════════════════════════════════════════════════════════════
# Architecture Detection
# ═══════════════════════════════════════════════════════════════════

class TestArchitectureDetector:
    def test_detect_returns_list(self):
        detector = ArchitectureDetector()
        results = detector.detect(list(SAMPLE_SOURCES.keys()))
        assert isinstance(results, list)
        assert all(isinstance(r, ArchitectureInfo) for r in results)

    def test_detect_mvc_signals(self):
        paths = [
            "app/controllers/user.py",
            "app/models/user.py",
            "app/views/index.html",
            "app/templates/base.html",
        ]
        detector = ArchitectureDetector()
        results = detector.detect(paths)
        mvc = [r for r in results if r.architecture == Architecture.MVC]
        assert len(mvc) > 0
        assert mvc[0].confidence > 0

    def test_detect_components(self):
        detector = ArchitectureDetector()
        components = detector.detect_components(list(SAMPLE_SOURCES.keys()))
        assert isinstance(components, dict)

    def test_detect_repository_pattern(self):
        paths = ["app/repositories/user_repo.py", "app/repositories/__init__.py"]
        detector = ArchitectureDetector()
        results = detector.detect(paths)
        repo_pat = [
            r for r in results
            if r.architecture == Architecture.REPOSITORY_PATTERN
        ]
        assert len(repo_pat) > 0

    def test_empty_paths(self):
        detector = ArchitectureDetector()
        results = detector.detect([])
        assert isinstance(results, list)


# ═══════════════════════════════════════════════════════════════════
# Circular Dependencies
# ═══════════════════════════════════════════════════════════════════

class TestCircularDependencies:
    def test_detect_direct_cycle(self):
        graph = {"a.py": ["b.py"], "b.py": ["a.py"]}
        detector = CircularDependencyDetector()
        cycles = detector.detect(graph)
        assert len(cycles) >= 1
        assert any(c.length >= 2 for c in cycles)

    def test_detect_multi_file_cycle(self):
        graph = {"a.py": ["b.py"], "b.py": ["c.py"], "c.py": ["a.py"]}
        detector = CircularDependencyDetector()
        cycles = detector.detect(graph)
        assert len(cycles) >= 1

    def test_no_cycle(self):
        graph = {"a.py": ["b.py"], "b.py": ["c.py"], "c.py": []}
        detector = CircularDependencyDetector()
        cycles = detector.detect(graph)
        assert len(cycles) == 0

    def test_detect_package_cycles(self):
        graph = {
            "pkg_a/mod.py": ["pkg_b/mod.py"],
            "pkg_b/mod.py": ["pkg_a/mod.py"],
        }
        detector = CircularDependencyDetector()
        cycles = detector.detect_package_cycles(graph)
        assert len(cycles) >= 1
        assert all(c.is_package_level for c in cycles)

    def test_empty_graph(self):
        detector = CircularDependencyDetector()
        cycles = detector.detect({})
        assert cycles == []

    def test_severity_assignment(self):
        # Direct 2-node cycle should be HIGH
        graph = {"a.py": ["b.py"], "b.py": ["a.py"]}
        detector = CircularDependencyDetector()
        cycles = detector.detect(graph)
        assert all(c.severity in (Severity.HIGH, Severity.MEDIUM) for c in cycles)


# ═══════════════════════════════════════════════════════════════════
# Hotspot Analysis
# ═══════════════════════════════════════════════════════════════════

class TestHotspotAnalyzer:
    def test_analyze_returns_hotspots(self):
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze(SAMPLE_SOURCES)
        assert isinstance(hotspots, list)
        assert all(isinstance(h, Hotspot) for h in hotspots)

    def test_risk_scores_bounded(self):
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze(SAMPLE_SOURCES)
        for h in hotspots:
            assert 0.0 <= h.risk_score <= 1.0

    def test_top_risky(self):
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze(SAMPLE_SOURCES)
        top = analyzer.top_risky(hotspots, n=3)
        assert len(top) <= 3
        if len(top) >= 2:
            assert top[0].risk_score >= top[1].risk_score

    def test_top_complex(self):
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze(
            SAMPLE_SOURCES,
            complexity_data={"app/services/user_service.py": 15},
        )
        top = analyzer.top_complex(hotspots, n=5)
        assert isinstance(top, list)

    def test_top_coupled(self):
        analyzer = HotspotAnalyzer()
        dep_graph = {"a.py": ["b.py", "c.py"], "b.py": ["a.py"]}
        hotspots = analyzer.analyze(SAMPLE_SOURCES, dep_graph)
        top = analyzer.top_coupled(hotspots, n=5)
        assert isinstance(top, list)

    def test_empty_sources(self):
        analyzer = HotspotAnalyzer()
        hotspots = analyzer.analyze({})
        assert hotspots == []


# ═══════════════════════════════════════════════════════════════════
# Layer Violations
# ═══════════════════════════════════════════════════════════════════

class TestLayerViolations:
    def test_detect_violation(self):
        classifications = [
            FileClassification(
                "ctrl.py", FileCategory.CONTROLLER, 0.9,
                layer=Layer.CONTROLLER,
            ),
            FileClassification(
                "infra.py", FileCategory.INFRASTRUCTURE, 0.9,
                layer=Layer.INFRASTRUCTURE,
            ),
        ]
        dep_graph = {"ctrl.py": ["infra.py"]}
        detector = LayerViolationDetector()
        violations = detector.detect(classifications, dep_graph)
        assert len(violations) >= 1
        assert violations[0].source_layer == Layer.CONTROLLER
        assert violations[0].target_layer == Layer.INFRASTRUCTURE

    def test_no_violation_safe_import(self):
        classifications = [
            FileClassification(
                "svc.py", FileCategory.SERVICE, 0.9,
                layer=Layer.SERVICE,
            ),
            FileClassification(
                "model.py", FileCategory.MODEL, 0.9,
                layer=Layer.MODEL,
            ),
        ]
        dep_graph = {"svc.py": ["model.py"]}
        detector = LayerViolationDetector()
        violations = detector.detect(classifications, dep_graph)
        assert len(violations) == 0

    def test_get_rules(self):
        detector = LayerViolationDetector()
        rules = detector.get_rules()
        assert isinstance(rules, dict)
        assert Layer.CONTROLLER in rules

    def test_add_custom_rule(self):
        detector = LayerViolationDetector()
        detector.add_rule(Layer.API, frozenset({Layer.DATABASE}))
        rules = detector.get_rules()
        assert Layer.API in rules


# ═══════════════════════════════════════════════════════════════════
# Change Impact Analysis
# ═══════════════════════════════════════════════════════════════════

class TestChangeImpact:
    def test_calculate_impact(self):
        dep_graph = {
            "a.py": ["b.py"],
            "b.py": ["c.py"],
            "c.py": [],
            "d.py": ["a.py"],
        }
        analyzer = ChangeImpactAnalyzer()
        impact = analyzer.calculate_impact(["c.py"], dep_graph)
        assert isinstance(impact, ChangeImpact)
        assert "c.py" in impact.changed_files

    def test_transitive_dependents(self):
        dep_graph = {
            "a.py": ["b.py"],
            "b.py": ["c.py"],
            "c.py": [],
        }
        analyzer = ChangeImpactAnalyzer()
        dependents = analyzer.transitive_dependents("c.py", dep_graph)
        assert "b.py" in dependents
        assert "a.py" in dependents

    def test_affected_modules(self):
        dep_graph = {"a.py": ["b.py"], "b.py": []}
        analyzer = ChangeImpactAnalyzer()
        modules = analyzer.affected_modules(["b.py"], dep_graph)
        # May return module names (without .py) or file paths
        assert any("a" in m for m in modules)

    def test_risk_score_bounded(self):
        dep_graph = {"a.py": ["b.py"], "b.py": []}
        analyzer = ChangeImpactAnalyzer()
        impact = analyzer.calculate_impact(["b.py"], dep_graph)
        assert 0.0 <= impact.risk_score <= 1.0

    def test_empty_changed_files(self):
        analyzer = ChangeImpactAnalyzer()
        impact = analyzer.calculate_impact([], {"a.py": []})
        assert impact.risk_score == 0.0


# ═══════════════════════════════════════════════════════════════════
# Repository Metadata
# ═══════════════════════════════════════════════════════════════════

class TestRepositoryMetadata:
    def test_collect_basic_metadata(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(
            list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES
        )
        assert isinstance(metadata, RepositoryMetadata)
        assert metadata.total_files > 0
        assert metadata.total_python_files > 0

    def test_detect_languages(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(["app.py", "style.css", "README.md"])
        assert "Python" in metadata.languages

    def test_modules_collected(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(
            list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES
        )
        assert len(metadata.modules) > 0
        assert all(isinstance(m, ModuleInfo) for m in metadata.modules)

    def test_packages_collected(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(list(SAMPLE_SOURCES.keys()))
        assert isinstance(metadata.packages, list)

    def test_entry_points_detected(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(["main.py", "app.py", "utils.py"])
        assert "main.py" in metadata.entry_points
        assert "app.py" in metadata.entry_points

    def test_config_files_detected(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect(
            ["pyproject.toml", "requirements.txt", "app.py"]
        )
        assert "pyproject.toml" in metadata.config_files

    def test_empty_file_list(self):
        collector = RepositoryMetadataCollector()
        metadata = collector.collect([])
        assert metadata.total_files == 0


# ═══════════════════════════════════════════════════════════════════
# File Classifier
# ═══════════════════════════════════════════════════════════════════

class TestFileClassifier:
    def test_classify_controller(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/controllers/user_controller.py")
        assert fc.category == FileCategory.CONTROLLER

    def test_classify_test(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("tests/test_user.py")
        assert fc.category == FileCategory.TEST

    def test_classify_model(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/models/user.py")
        assert fc.category == FileCategory.MODEL

    def test_classify_service(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/services/user_service.py")
        assert fc.category == FileCategory.SERVICE

    def test_classify_repository_file(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/repositories/user_repo.py")
        assert fc.category == FileCategory.REPOSITORY

    def test_classify_utility(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/utils/helpers.py")
        assert fc.category == FileCategory.UTILITY

    def test_classify_config(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("config/settings.py")
        assert fc.category == FileCategory.CONFIGURATION

    def test_classify_unknown(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/random_file_xyz.py")
        assert fc.category == FileCategory.UNKNOWN or fc.confidence < 0.5

    def test_classify_batch(self):
        classifier = FileClassifier()
        results = classifier.classify(list(SAMPLE_SOURCES.keys()))
        assert len(results) == len(SAMPLE_SOURCES)
        assert all(isinstance(r, FileClassification) for r in results)

    def test_get_layer(self):
        classifier = FileClassifier()
        assert classifier.get_layer(FileCategory.CONTROLLER) == Layer.CONTROLLER
        assert classifier.get_layer(FileCategory.TEST) == Layer.TEST

    def test_confidence_scores(self):
        classifier = FileClassifier()
        fc = classifier.classify_file("app/controllers/user_controller.py")
        assert fc.confidence > 0


# ═══════════════════════════════════════════════════════════════════
# Repository Graph
# ═══════════════════════════════════════════════════════════════════

class TestRepositoryGraph:
    def test_add_file_node(self):
        g = RepositoryGraph()
        node = g.add_file("test.py")
        assert isinstance(node, RepoGraphNode)
        assert node.repo_kind == RepoNodeKind.FILE

    def test_add_package_node(self):
        g = RepositoryGraph()
        node = g.add_package("app/models")
        assert node.repo_kind == RepoNodeKind.PACKAGE

    def test_add_dependency_edge(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        edge = g.add_dependency("a.py", "b.py")
        assert isinstance(edge, RepoGraphEdge)
        assert edge.repo_kind == RepoEdgeKind.IMPORTS

    def test_inherited_bfs(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        g.add_file("c.py")
        g.add_dependency("a.py", "b.py")
        g.add_dependency("b.py", "c.py")
        # bfs returns GraphNode objects; extract IDs
        visited = [n.id if hasattr(n, 'id') else str(n) for n in g.bfs("a.py")]
        assert "b.py" in visited
        assert "c.py" in visited

    def test_inherited_find_path(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        g.add_file("c.py")
        g.add_dependency("a.py", "b.py")
        g.add_dependency("b.py", "c.py")
        path = g.find_path("a.py", "c.py")
        assert path is not None
        assert path[0] == "a.py"
        assert path[-1] == "c.py"

    def test_inherited_has_cycle(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        g.add_dependency("a.py", "b.py")
        g.add_dependency("b.py", "a.py")
        assert g.has_cycle() is True

    def test_build_from_analysis(self):
        g = RepositoryGraph()
        files = ["a.py", "b.py"]
        dep_graph = {"a.py": ["b.py"]}
        classifications = [
            FileClassification("a.py", FileCategory.SERVICE, 0.9, layer=Layer.SERVICE),
            FileClassification("b.py", FileCategory.MODEL, 0.9, layer=Layer.MODEL),
        ]
        g.build_from_analysis(files, dep_graph, classifications)
        assert len(g.get_file_nodes()) == 2
        assert len(g.get_layer_nodes()) >= 2

    def test_get_file_dependencies(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        g.add_dependency("a.py", "b.py")
        deps = g.get_file_dependencies("a.py")
        assert "b.py" in deps

    def test_get_file_dependents(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        g.add_file("b.py")
        g.add_dependency("a.py", "b.py")
        dependents = g.get_file_dependents("b.py")
        assert "a.py" in dependents

    def test_to_dict(self):
        g = RepositoryGraph()
        g.add_file("a.py")
        d = g.to_dict()
        assert "node_count" in d
        assert d["file_count"] == 1

    def test_layer_membership(self):
        g = RepositoryGraph()
        g.add_file("svc.py", layer=Layer.SERVICE)
        g.add_layer_membership("svc.py", Layer.SERVICE)
        files = g.get_files_in_layer(Layer.SERVICE)
        assert "svc.py" in files


# ═══════════════════════════════════════════════════════════════════
# Query Engine (Integration)
# ═══════════════════════════════════════════════════════════════════

class TestQueryEngine:
    def test_analyze_and_query(self):
        engine = RepositoryQueryEngine()
        engine.analyze(
            list(SAMPLE_SOURCES.keys()),
            SAMPLE_SOURCES,
        )
        assert engine.metadata is not None
        assert engine.dependency_graph is not None
        assert engine.classifications is not None

    def test_find_hotspots(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        hotspots = engine.find_hotspots(n=5)
        assert isinstance(hotspots, list)

    def test_find_architecture(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        architectures = engine.find_architecture()
        assert isinstance(architectures, list)

    def test_find_cycles(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        cycles = engine.find_cycles()
        assert isinstance(cycles, list)

    def test_find_dependents(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        deps = engine.find_dependents("app/models/user.py")
        assert isinstance(deps, list)

    def test_find_dependencies(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        deps = engine.find_dependencies("app/controllers/user_controller.py")
        assert isinstance(deps, list)

    def test_find_layer_violations(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        violations = engine.find_layer_violations()
        assert isinstance(violations, list)

    def test_find_change_impact(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        impact = engine.find_change_impact(["app/models/user.py"])
        assert isinstance(impact, ChangeImpact)

    def test_find_repository_summary(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        summary = engine.find_repository_summary()
        assert isinstance(summary, RepositorySummary)
        assert summary.total_modules > 0
        assert 0.0 <= summary.health_score <= 1.0

    def test_repository_graph_accessible(self):
        engine = RepositoryQueryEngine()
        engine.analyze(list(SAMPLE_SOURCES.keys()), SAMPLE_SOURCES)
        graph = engine.repository_graph
        assert graph is not None
        assert isinstance(graph, RepositoryGraph)

    def test_empty_analysis(self):
        engine = RepositoryQueryEngine()
        engine.analyze([], {})
        summary = engine.find_repository_summary()
        assert summary.total_modules == 0
