"""
Propagation Engine — deterministic taint / value propagation
over a DataFlowGraph.

Given a set of initially-tainted nodes (sources), the engine
propagates taint labels forward through all reachable data-flow
edges, respecting aliasing.
"""

from __future__ import annotations

from typing import List, Set, Optional, Dict

from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.constants import DataFlowEdgeKind
from app.analysis.dataflow.models import TaintLabel, FlowPath
from app.analysis.dataflow.propagation.alias_tracker import AliasTracker
from app.analysis.dataflow.propagation.propagation_models import (
    PropagationChain,
    PropagationStep,
)


class PropagationEngine:
    """Deterministic forward-propagation of taint labels."""

    def __init__(self, graph: DataFlowGraph):
        self.graph = graph
        self.alias_tracker = AliasTracker()
        self._build_aliases()

    # ── alias construction ───────────────────────────────────────

    def _build_aliases(self) -> None:
        """Scan assignment / alias edges and register aliases."""
        for edge in self.graph.get_df_edges():
            if edge.df_kind in (
                DataFlowEdgeKind.ASSIGNMENT,
                DataFlowEdgeKind.ALIAS,
            ):
                src = self.graph.get_df_node(edge.source)
                tgt = self.graph.get_df_node(edge.target)
                if src and tgt:
                    self.alias_tracker.record_alias(tgt.name, src.name)

    # ── forward propagation ──────────────────────────────────────

    def propagate(self) -> List[DataFlowNode]:
        """Propagate taint from all source nodes forward.

        Returns the list of newly-tainted nodes.
        """
        worklist: List[str] = []
        for node in self.graph.get_df_nodes():
            if node.is_tainted():
                worklist.append(node.id)

        visited: Set[str] = set()
        newly_tainted: List[DataFlowNode] = []

        while worklist:
            current_id = worklist.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            current = self.graph.get_df_node(current_id)
            if current is None or not current.is_tainted():
                continue

            # propagate along outgoing data-flow edges
            for edge in self.graph.get_outgoing_edges(current_id):
                if not isinstance(edge, DataFlowEdge):
                    continue
                target = self.graph.get_df_node(edge.target)
                if target is None:
                    continue

                old_count = len(target.taint_labels)
                for label in current.taint_labels:
                    target.add_taint(label)

                if len(target.taint_labels) > old_count:
                    newly_tainted.append(target)
                    if target.id not in visited:
                        worklist.append(target.id)

            # propagate via aliases
            aliases = self.alias_tracker.get_aliases(current.name)
            for alias_name in aliases:
                for alias_node in self.graph.get_nodes_by_name(alias_name):
                    old_count = len(alias_node.taint_labels)
                    for label in current.taint_labels:
                        alias_node.add_taint(label)
                    if len(alias_node.taint_labels) > old_count:
                        newly_tainted.append(alias_node)
                        if alias_node.id not in visited:
                            worklist.append(alias_node.id)

        return newly_tainted

    # ── chain tracing ────────────────────────────────────────────

    def trace_chain(
        self, start_id: str, end_id: str
    ) -> Optional[PropagationChain]:
        """Build the propagation chain between two nodes."""
        path_ids = self.graph.find_path(start_id, end_id)
        if path_ids is None:
            return None

        chain = PropagationChain()
        for i in range(len(path_ids) - 1):
            src_id = path_ids[i]
            tgt_id = path_ids[i + 1]
            # find the connecting edge
            edge_kind = DataFlowEdgeKind.ASSIGNMENT
            edge_line: Optional[int] = None
            for edge in self.graph.get_outgoing_edges(src_id):
                if isinstance(edge, DataFlowEdge) and edge.target == tgt_id:
                    edge_kind = edge.df_kind
                    edge_line = edge.line
                    break
            chain.steps.append(
                PropagationStep(
                    from_node_id=src_id,
                    to_node_id=tgt_id,
                    edge_kind=edge_kind,
                    line=edge_line,
                )
            )
        return chain

    def find_tainted_sinks(self) -> List[FlowPath]:
        """Find all source→sink flow paths where the sink is tainted."""
        results: List[FlowPath] = []
        sources = self.graph.get_sources()
        sinks = self.graph.get_sinks()

        for source in sources:
            for sink in sinks:
                if not sink.is_tainted():
                    continue
                path_ids = self.graph.find_path(source.id, sink.id)
                if path_ids:
                    results.append(
                        FlowPath(
                            source_node_id=source.id,
                            sink_node_id=sink.id,
                            path_node_ids=path_ids,
                            taint_labels=list(source.taint_labels),
                        )
                    )
                else:
                    # Taint reached sink via alias propagation —
                    # still a valid finding, construct synthetic path.
                    results.append(
                        FlowPath(
                            source_node_id=source.id,
                            sink_node_id=sink.id,
                            path_node_ids=[source.id, sink.id],
                            taint_labels=list(source.taint_labels),
                        )
                    )
        return results
