"""
Repository Graph — extends the shared Graph Foundation.

Represents files, packages, modules, dependencies, architecture,
layers, and relationships as a directed graph. Reuses all traversal,
path-finding, and cycle detection from the Graph base class.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Any

from app.analysis.graph.graph_base import Graph
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_edge import GraphEdge
from app.analysis.graph.graph_types import NodeKind, EdgeKind

from app.analysis.repository.constants import RepoNodeKind, RepoEdgeKind, Layer
from app.analysis.repository.models import FileClassification


# ═══════════════════════════════════════════════════════════════════
# Repository Graph Node
# ═══════════════════════════════════════════════════════════════════

class RepoGraphNode(GraphNode):
    """A node in the Repository Graph."""

    def __init__(
        self,
        node_id: str,
        repo_kind: RepoNodeKind,
        label: Optional[str] = None,
        layer: Optional[Layer] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        merged = properties or {}
        merged["repo_kind"] = repo_kind.value
        if layer:
            merged["layer"] = layer.value
        super().__init__(
            node_id=node_id,
            kind=NodeKind.GENERIC,
            label=label or node_id,
            properties=merged,
        )
        self.repo_kind: RepoNodeKind = repo_kind
        self.layer: Optional[Layer] = layer


# ═══════════════════════════════════════════════════════════════════
# Repository Graph Edge
# ═══════════════════════════════════════════════════════════════════

class RepoGraphEdge(GraphEdge):
    """A directed edge in the Repository Graph."""

    def __init__(
        self,
        source: str,
        target: str,
        repo_kind: RepoEdgeKind,
        properties: Optional[Dict[str, Any]] = None,
    ):
        merged = properties or {}
        merged["repo_kind"] = repo_kind.value
        super().__init__(
            source=source,
            target=target,
            kind=EdgeKind.GENERIC,
            label=repo_kind.value,
            properties=merged,
        )
        self.repo_kind: RepoEdgeKind = repo_kind


# ═══════════════════════════════════════════════════════════════════
# Repository Graph
# ═══════════════════════════════════════════════════════════════════

class RepositoryGraph(Graph):
    """Directed graph representing the repository structure.

    Inherits ``add_node``, ``add_edge``, ``get_successors``,
    ``get_predecessors``, ``dfs``, ``bfs``, ``find_path``,
    ``has_cycle`` from the shared :class:`Graph` foundation.
    """

    def __init__(self) -> None:
        super().__init__()

    # ── build helpers ────────────────────────────────────────────

    def add_file(
        self,
        file_path: str,
        layer: Optional[Layer] = None,
    ) -> RepoGraphNode:
        node = RepoGraphNode(
            node_id=file_path,
            repo_kind=RepoNodeKind.FILE,
            label=file_path,
            layer=layer,
        )
        self.add_node(node)
        return node

    def add_package(self, package_path: str) -> RepoGraphNode:
        node = RepoGraphNode(
            node_id=f"pkg:{package_path}",
            repo_kind=RepoNodeKind.PACKAGE,
            label=package_path,
        )
        self.add_node(node)
        return node

    def add_module(self, module_name: str) -> RepoGraphNode:
        node = RepoGraphNode(
            node_id=f"mod:{module_name}",
            repo_kind=RepoNodeKind.MODULE,
            label=module_name,
        )
        self.add_node(node)
        return node

    def add_layer_node(self, layer: Layer) -> RepoGraphNode:
        node = RepoGraphNode(
            node_id=f"layer:{layer.value}",
            repo_kind=RepoNodeKind.LAYER,
            label=layer.value,
            layer=layer,
        )
        self.add_node(node)
        return node

    def add_dependency(self, source: str, target: str) -> RepoGraphEdge:
        edge = RepoGraphEdge(source, target, RepoEdgeKind.IMPORTS)
        self.add_edge(edge)
        return edge

    def add_containment(self, parent: str, child: str) -> RepoGraphEdge:
        edge = RepoGraphEdge(parent, child, RepoEdgeKind.CONTAINS)
        self.add_edge(edge)
        return edge

    def add_layer_membership(self, file_path: str, layer: Layer) -> RepoGraphEdge:
        layer_id = f"layer:{layer.value}"
        if layer_id not in self.nodes:
            self.add_layer_node(layer)
        edge = RepoGraphEdge(file_path, layer_id, RepoEdgeKind.BELONGS_TO_LAYER)
        self.add_edge(edge)
        return edge

    def add_package_membership(
        self, file_path: str, package_path: str
    ) -> RepoGraphEdge:
        pkg_id = f"pkg:{package_path}"
        if pkg_id not in self.nodes:
            self.add_package(package_path)
        edge = RepoGraphEdge(file_path, pkg_id, RepoEdgeKind.BELONGS_TO_PACKAGE)
        self.add_edge(edge)
        return edge

    # ── build from analysis results ──────────────────────────────

    def build_from_analysis(
        self,
        file_paths: List[str],
        dependency_graph: Optional[Dict[str, List[str]]] = None,
        file_classifications: Optional[List[FileClassification]] = None,
    ) -> None:
        """Populate the graph from analysis results."""
        # Classification lookup
        class_map: Dict[str, FileClassification] = {}
        if file_classifications:
            for fc in file_classifications:
                class_map[fc.file_path] = fc

        # Add file nodes
        for fp in file_paths:
            fc = class_map.get(fp)
            layer = fc.layer if fc else None
            self.add_file(fp, layer=layer)

            # Layer membership
            if layer and layer != Layer.UNKNOWN:
                self.add_layer_membership(fp, layer)

            # Package membership
            pkg = self._file_to_package(fp)
            if pkg:
                self.add_package_membership(fp, pkg)

        # Add dependency edges
        if dependency_graph:
            for src, targets in dependency_graph.items():
                for tgt in targets:
                    if src in self.nodes and tgt in self.nodes:
                        self.add_dependency(src, tgt)

    # ── query helpers ────────────────────────────────────────────

    def get_file_nodes(self) -> List[RepoGraphNode]:
        return [
            n
            for n in self.nodes.values()
            if isinstance(n, RepoGraphNode)
            and n.repo_kind == RepoNodeKind.FILE
        ]

    def get_package_nodes(self) -> List[RepoGraphNode]:
        return [
            n
            for n in self.nodes.values()
            if isinstance(n, RepoGraphNode)
            and n.repo_kind == RepoNodeKind.PACKAGE
        ]

    def get_layer_nodes(self) -> List[RepoGraphNode]:
        return [
            n
            for n in self.nodes.values()
            if isinstance(n, RepoGraphNode)
            and n.repo_kind == RepoNodeKind.LAYER
        ]

    def get_files_in_layer(self, layer: Layer) -> List[str]:
        layer_id = f"layer:{layer.value}"
        if layer_id not in self.nodes:
            return []
        return [
            e.source
            for e in self.get_incoming_edges(layer_id)
            if isinstance(e, RepoGraphEdge)
            and e.repo_kind == RepoEdgeKind.BELONGS_TO_LAYER
        ]

    def get_file_dependencies(self, file_path: str) -> List[str]:
        return [
            e.target
            for e in self.get_outgoing_edges(file_path)
            if isinstance(e, RepoGraphEdge)
            and e.repo_kind == RepoEdgeKind.IMPORTS
        ]

    def get_file_dependents(self, file_path: str) -> List[str]:
        return [
            e.source
            for e in self.get_incoming_edges(file_path)
            if isinstance(e, RepoGraphEdge)
            and e.repo_kind == RepoEdgeKind.IMPORTS
        ]

    # ── serialization ────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "file_count": len(self.get_file_nodes()),
            "package_count": len(self.get_package_nodes()),
            "layer_count": len(self.get_layer_nodes()),
        }

    # ── internal helpers ─────────────────────────────────────────

    @staticmethod
    def _file_to_package(file_path: str) -> Optional[str]:
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return "/".join(parts[:-1])
        return None
