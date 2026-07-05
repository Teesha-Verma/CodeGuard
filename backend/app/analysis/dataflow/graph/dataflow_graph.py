"""
Data Flow Graph — extends the shared Graph base.

Reuses all traversal / path-finding / cycle-detection from GraphBase.
Adds data-flow-specific query helpers.
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional, Any

from app.analysis.graph.graph_base import Graph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.constants import DataFlowNodeKind, DataFlowEdgeKind


class DataFlowGraph(Graph):
    """Directed graph of data-flow relationships.

    Inherits ``add_node``, ``add_edge``, ``get_successors``,
    ``get_predecessors``, ``dfs``, ``bfs``, ``find_path``,
    ``has_cycle`` from the shared :class:`Graph` foundation.
    """

    def __init__(self, module_name: str = ""):
        super().__init__()
        self.module_name: str = module_name

    # ── typed accessors ──────────────────────────────────────────

    def get_df_node(self, node_id: str) -> Optional[DataFlowNode]:
        node = self.get_node(node_id)
        return node if isinstance(node, DataFlowNode) else None

    def get_df_nodes(self) -> List[DataFlowNode]:
        return [n for n in self.nodes.values() if isinstance(n, DataFlowNode)]

    def get_df_edges(self) -> List[DataFlowEdge]:
        return [e for e in self.edges if isinstance(e, DataFlowEdge)]

    # ── flow queries (reuse inherited BFS / DFS) ─────────────────

    def reachable_nodes(self, start_id: str) -> Set[str]:
        """All node ids reachable from *start_id* (excluding itself)."""
        result: Set[str] = set()
        for node in self.bfs(start_id):
            if node.id != start_id:
                result.add(node.id)
        return result

    def trace_flow(self, start_id: str) -> List[DataFlowNode]:
        """Returns all DataFlowNodes reachable from *start_id* via BFS."""
        return [
            n for n in self.bfs(start_id)
            if isinstance(n, DataFlowNode) and n.id != start_id
        ]

    def find_flow_between(
        self, source_id: str, sink_id: str
    ) -> Optional[List[str]]:
        """Find a data-flow path between two nodes (delegates to inherited find_path)."""
        return self.find_path(source_id, sink_id)

    def trace_path(
        self, start_id: str, end_id: str
    ) -> Optional[List[DataFlowNode]]:
        """Like ``find_flow_between`` but returns full node objects."""
        path_ids = self.find_path(start_id, end_id)
        if path_ids is None:
            return None
        result = []
        for nid in path_ids:
            node = self.get_df_node(nid)
            if node:
                result.append(node)
        return result

    # ── filtered queries ─────────────────────────────────────────

    def get_sources(self) -> List[DataFlowNode]:
        return [n for n in self.get_df_nodes() if n.is_source]

    def get_sinks(self) -> List[DataFlowNode]:
        return [n for n in self.get_df_nodes() if n.is_sink]

    def get_tainted_nodes(self) -> List[DataFlowNode]:
        return [n for n in self.get_df_nodes() if n.is_tainted()]

    def get_nodes_by_kind(self, kind: DataFlowNodeKind) -> List[DataFlowNode]:
        return [n for n in self.get_df_nodes() if n.df_kind == kind]

    def get_nodes_by_name(self, name: str) -> List[DataFlowNode]:
        return [n for n in self.get_df_nodes() if n.name == name]

    def get_edges_by_kind(self, kind: DataFlowEdgeKind) -> List[DataFlowEdge]:
        return [e for e in self.get_df_edges() if e.df_kind == kind]

    # ── serialization ────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "nodes": [n.to_dict() for n in self.get_df_nodes()],
            "edges": [e.to_dict() for e in self.get_df_edges()],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }
