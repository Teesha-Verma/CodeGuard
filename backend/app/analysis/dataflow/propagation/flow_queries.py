"""
Flow Queries — high-level query API over a DataFlowGraph.

All queries are deterministic and reuse the inherited BFS / DFS /
path-finding from the shared Graph foundation.
"""

from __future__ import annotations

from typing import List, Set, Optional, Dict

from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.constants import DataFlowNodeKind, DataFlowEdgeKind
from app.analysis.dataflow.models import FlowPath


def get_sources(graph: DataFlowGraph) -> List[DataFlowNode]:
    """Return all nodes marked as taint sources."""
    return graph.get_sources()


def get_sinks(graph: DataFlowGraph) -> List[DataFlowNode]:
    """Return all nodes marked as sinks."""
    return graph.get_sinks()


def trace_variable(
    graph: DataFlowGraph, variable_name: str
) -> List[DataFlowNode]:
    """Trace all nodes reachable from any node named *variable_name*."""
    results: List[DataFlowNode] = []
    for start_node in graph.get_nodes_by_name(variable_name):
        for reached in graph.trace_flow(start_node.id):
            if reached not in results:
                results.append(reached)
    return results


def trace_function(
    graph: DataFlowGraph, function_name: str
) -> List[DataFlowNode]:
    """Trace all data-flow nodes reachable from a call to *function_name*."""
    results: List[DataFlowNode] = []
    for node in graph.get_df_nodes():
        if (
            node.df_kind == DataFlowNodeKind.CALL_RESULT
            and function_name in node.name
        ):
            for reached in graph.trace_flow(node.id):
                if reached not in results:
                    results.append(reached)
    return results


def trace_to_sink(
    graph: DataFlowGraph, source_id: str
) -> List[FlowPath]:
    """Find all flow paths from *source_id* to any sink."""
    paths: List[FlowPath] = []
    source = graph.get_df_node(source_id)
    if source is None:
        return paths

    for sink in graph.get_sinks():
        path_ids = graph.find_path(source_id, sink.id)
        if path_ids:
            paths.append(
                FlowPath(
                    source_node_id=source_id,
                    sink_node_id=sink.id,
                    path_node_ids=path_ids,
                    taint_labels=list(source.taint_labels),
                )
            )
    return paths


def trace_from_source(
    graph: DataFlowGraph, sink_id: str
) -> List[FlowPath]:
    """Find all flow paths from any source to *sink_id*."""
    paths: List[FlowPath] = []

    for source in graph.get_sources():
        path_ids = graph.find_path(source.id, sink_id)
        if path_ids:
            paths.append(
                FlowPath(
                    source_node_id=source.id,
                    sink_node_id=sink_id,
                    path_node_ids=path_ids,
                    taint_labels=list(source.taint_labels),
                )
            )
    return paths


def reachable_sinks(
    graph: DataFlowGraph, source_id: str
) -> List[DataFlowNode]:
    """Return all sink nodes reachable from *source_id*."""
    reachable_ids = graph.reachable_nodes(source_id)
    return [
        n for n in graph.get_sinks()
        if n.id in reachable_ids
    ]


def reachable_sources(
    graph: DataFlowGraph, sink_id: str
) -> List[DataFlowNode]:
    """Return all source nodes that can reach *sink_id* (reverse search)."""
    results: List[DataFlowNode] = []
    for source in graph.get_sources():
        path = graph.find_path(source.id, sink_id)
        if path is not None:
            results.append(source)
    return results


def has_taint_flow(
    graph: DataFlowGraph, source_id: str, sink_id: str
) -> bool:
    """Check whether a data-flow path exists from *source_id* to *sink_id*."""
    return graph.find_path(source_id, sink_id) is not None


def get_data_dependencies(
    graph: DataFlowGraph, node_id: str
) -> List[DataFlowNode]:
    """Return the direct data-flow predecessors of *node_id*."""
    results: List[DataFlowNode] = []
    for edge in graph.get_incoming_edges(node_id):
        node = graph.get_df_node(edge.source)
        if node:
            results.append(node)
    return results


def get_reverse_dependencies(
    graph: DataFlowGraph, node_id: str
) -> List[DataFlowNode]:
    """Return the direct data-flow successors of *node_id*."""
    results: List[DataFlowNode] = []
    for edge in graph.get_outgoing_edges(node_id):
        node = graph.get_df_node(edge.target)
        if node:
            results.append(node)
    return results


def get_flow_summary(graph: DataFlowGraph) -> Dict[str, int]:
    """Return a summary of the data-flow graph metrics."""
    return {
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "sources": len(graph.get_sources()),
        "sinks": len(graph.get_sinks()),
        "tainted_nodes": len(graph.get_tainted_nodes()),
        "variables": len(graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)),
        "parameters": len(graph.get_nodes_by_kind(DataFlowNodeKind.PARAMETER)),
        "call_results": len(graph.get_nodes_by_kind(DataFlowNodeKind.CALL_RESULT)),
        "literals": len(graph.get_nodes_by_kind(DataFlowNodeKind.LITERAL)),
    }
