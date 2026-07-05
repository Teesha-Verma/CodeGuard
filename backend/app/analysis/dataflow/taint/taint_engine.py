"""
Taint Engine — orchestrates source detection, propagation, and sink
detection to produce vulnerability findings.

Supports:
- intra-function taint
- inter-function taint (via Call Graph)
- cross-file taint (via Call Graph module resolution)
- alias / attribute / collection taint

Reuses existing CFG and Call Graph — does NOT rebuild them.
"""

from __future__ import annotations

from typing import List, Dict, Optional

from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_builder import DataFlowBuilder
from app.analysis.dataflow.propagation.propagation_engine import PropagationEngine
from app.analysis.dataflow.taint.source_detector import SourceDetector
from app.analysis.dataflow.taint.sink_detector import SinkDetector
from app.analysis.dataflow.models import FlowPath, TaintLabel


class TaintEngine:
    """End-to-end deterministic taint analysis.

    Usage::

        engine = TaintEngine()
        engine.add_module("views", views_source)
        engine.add_module("service", service_source)
        flows = engine.run()
    """

    def __init__(
        self,
        extra_sinks: Optional[Dict[str, str]] = None,
    ):
        self.extra_sinks = extra_sinks
        # module_name → DataFlowGraph
        self._module_graphs: Dict[str, DataFlowGraph] = {}
        # merged graph for cross-module analysis
        self._merged_graph: Optional[DataFlowGraph] = None
        self._propagation_engine: Optional[PropagationEngine] = None

    # ── module registration ──────────────────────────────────────

    def add_module(
        self,
        module_name: str,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> DataFlowGraph:
        """Parse a module and add it to the analysis."""
        builder = DataFlowBuilder(
            module_name=module_name, file_path=file_path
        )
        graph = builder.build(source_code)
        self._module_graphs[module_name] = graph
        return graph

    def add_graph(self, module_name: str, graph: DataFlowGraph) -> None:
        """Add a pre-built DataFlowGraph."""
        self._module_graphs[module_name] = graph

    # ── analysis ─────────────────────────────────────────────────

    def run(self) -> List[FlowPath]:
        """Execute the full taint analysis pipeline.

        1. Merge all module graphs
        2. Detect sources
        3. Detect sinks
        4. Propagate taint
        5. Find source→sink flows
        """
        self._merged_graph = self._merge_graphs()

        # Phase: source detection
        source_detector = SourceDetector(self._merged_graph)
        sources = source_detector.detect()

        # Phase: sink detection
        sink_detector = SinkDetector(
            self._merged_graph, extra_sinks=self.extra_sinks
        )
        sinks = sink_detector.detect()

        # Phase: propagation
        self._propagation_engine = PropagationEngine(self._merged_graph)
        self._propagation_engine.propagate()

        # Phase: find tainted sinks
        flows = self._propagation_engine.find_tainted_sinks()
        return flows

    # ── accessors ────────────────────────────────────────────────

    @property
    def merged_graph(self) -> Optional[DataFlowGraph]:
        return self._merged_graph

    def get_sources(self) -> List[DataFlowNode]:
        if self._merged_graph is None:
            return []
        return self._merged_graph.get_sources()

    def get_sinks(self) -> List[DataFlowNode]:
        if self._merged_graph is None:
            return []
        return self._merged_graph.get_sinks()

    def get_tainted_nodes(self) -> List[DataFlowNode]:
        if self._merged_graph is None:
            return []
        return self._merged_graph.get_tainted_nodes()

    # ── graph merging (cross-file support) ───────────────────────

    def _merge_graphs(self) -> DataFlowGraph:
        """Merge per-module graphs into a single DataFlowGraph.

        Node IDs are prefixed with the module name to avoid collisions.
        Cross-module edges are added by matching return-value nodes
        to call-result nodes that reference the same function.
        """
        merged = DataFlowGraph(module_name="<merged>")

        # Maps for cross-module linking
        # function_fqn → list of return-value node IDs in merged graph
        return_nodes: Dict[str, List[str]] = {}
        # function_fqn → list of call-result node IDs in merged graph
        call_result_nodes: Dict[str, List[str]] = {}

        for mod_name, graph in self._module_graphs.items():
            id_map: Dict[str, str] = {}  # old_id → new_id

            # Copy nodes with prefixed IDs
            for node in graph.get_df_nodes():
                new_id = f"{mod_name}::{node.id}"
                id_map[node.id] = new_id

                new_node = DataFlowNode(
                    node_id=new_id,
                    df_kind=node.df_kind,
                    name=node.name,
                    line=node.line,
                    scope=f"{mod_name}.{node.scope}" if node.scope else mod_name,
                    file_path=node.file_path,
                    properties=dict(node.properties),
                )
                new_node.taint_labels = set(node.taint_labels)
                new_node.is_source = node.is_source
                new_node.is_sink = node.is_sink
                merged.add_node(new_node)

                # Track return / call-result nodes for cross-module linking
                if node.df_kind.value == "df_return_value" and node.scope:
                    fqn = f"{mod_name}.{node.scope}"
                    return_nodes.setdefault(fqn, []).append(new_id)
                if node.df_kind.value == "df_call_result":
                    func_name = node.name.rstrip("()")
                    call_result_nodes.setdefault(func_name, []).append(new_id)

            # Copy edges with remapped IDs
            for edge in graph.get_df_edges():
                new_src = id_map.get(edge.source, f"{mod_name}::{edge.source}")
                new_tgt = id_map.get(edge.target, f"{mod_name}::{edge.target}")
                from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
                new_edge = DataFlowEdge(
                    source=new_src,
                    target=new_tgt,
                    df_kind=edge.df_kind,
                    line=edge.line,
                    scope=edge.scope,
                )
                merged.add_edge(new_edge)

        # Cross-module linking: return nodes → call-result nodes
        for fqn, ret_ids in return_nodes.items():
            # Check if any call-result references this function
            for call_name, call_ids in call_result_nodes.items():
                if fqn.endswith(call_name) or call_name.endswith(fqn.split(".")[-1]):
                    for ret_id in ret_ids:
                        for call_id in call_ids:
                            from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
                            from app.analysis.dataflow.constants import DataFlowEdgeKind
                            cross_edge = DataFlowEdge(
                                source=ret_id,
                                target=call_id,
                                df_kind=DataFlowEdgeKind.RETURN_PROPAGATION,
                            )
                            merged.add_edge(cross_edge)

        return merged
