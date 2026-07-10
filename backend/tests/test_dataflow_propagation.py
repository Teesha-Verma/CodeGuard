"""
Tests for Phase 2 + 9 — Propagation Engine, Alias Tracker, Flow Queries.
"""

import pytest

from app.analysis.dataflow.constants import (
    DataFlowNodeKind,
    DataFlowEdgeKind,
    TaintKind,
)
from app.analysis.dataflow.models import TaintLabel
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_builder import DataFlowBuilder
from app.analysis.dataflow.propagation.alias_tracker import AliasTracker
from app.analysis.dataflow.propagation.propagation_engine import PropagationEngine
from app.analysis.dataflow.propagation import flow_queries


# ═══════════════════════════════════════════════════════════════════
# AliasTracker
# ═══════════════════════════════════════════════════════════════════

class TestAliasTracker:
    def test_simple_alias(self):
        at = AliasTracker()
        at.record_alias("y", "x")
        assert at.are_aliases("x", "y")
        assert at.are_aliases("y", "x")

    def test_transitive_alias(self):
        at = AliasTracker()
        at.record_alias("y", "x")
        at.record_alias("z", "y")
        aliases_of_x = at.get_aliases("x")
        assert "y" in aliases_of_x
        assert "z" in aliases_of_x

    def test_no_alias(self):
        at = AliasTracker()
        at.record_alias("y", "x")
        assert not at.are_aliases("x", "q")

    def test_chain_alias(self):
        at = AliasTracker()
        at.record_alias("b", "a")
        at.record_alias("c", "b")
        at.record_alias("d", "c")
        all_a = at.get_aliases("a")
        assert "b" in all_a
        assert "c" in all_a
        assert "d" in all_a


# ═══════════════════════════════════════════════════════════════════
# PropagationEngine
# ═══════════════════════════════════════════════════════════════════

class TestPropagationEngine:
    def _make_linear_graph(self):
        """src(tainted) → mid → sink."""
        g = DataFlowGraph("test")
        src = DataFlowNode("s", DataFlowNodeKind.CALL_RESULT, "input()", 1)
        mid = DataFlowNode("m", DataFlowNodeKind.VARIABLE, "x", 2)
        sink = DataFlowNode("k", DataFlowNodeKind.CALL_RESULT, "eval()", 3)
        src.add_taint(TaintLabel(TaintKind.USER_INPUT))
        src.is_source = True
        sink.is_sink = True
        g.add_node(src)
        g.add_node(mid)
        g.add_node(sink)
        g.add_edge(DataFlowEdge("s", "m", DataFlowEdgeKind.ASSIGNMENT, 2))
        g.add_edge(DataFlowEdge("m", "k", DataFlowEdgeKind.PARAMETER_PASS, 3))
        return g

    def test_forward_propagation(self):
        g = self._make_linear_graph()
        engine = PropagationEngine(g)
        newly_tainted = engine.propagate()
        mid = g.get_df_node("m")
        sink = g.get_df_node("k")
        assert mid.is_tainted()
        assert sink.is_tainted()

    def test_tainted_sinks_found(self):
        g = self._make_linear_graph()
        engine = PropagationEngine(g)
        engine.propagate()
        flows = engine.find_tainted_sinks()
        assert len(flows) >= 1
        assert flows[0].source_node_id == "s"
        assert flows[0].sink_node_id == "k"

    def test_trace_chain(self):
        g = self._make_linear_graph()
        engine = PropagationEngine(g)
        chain = engine.trace_chain("s", "k")
        assert chain is not None
        assert chain.length == 2
        assert chain.origin == "s"
        assert chain.destination == "k"

    def test_no_propagation_without_taint(self):
        g = DataFlowGraph("test")
        n1 = DataFlowNode("n1", DataFlowNodeKind.VARIABLE, "a", 1)
        n2 = DataFlowNode("n2", DataFlowNodeKind.VARIABLE, "b", 2)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(DataFlowEdge("n1", "n2", DataFlowEdgeKind.ASSIGNMENT, 2))
        engine = PropagationEngine(g)
        newly_tainted = engine.propagate()
        assert len(newly_tainted) == 0
        assert not n2.is_tainted()

    def test_branching_propagation(self):
        """Taint splits into two branches."""
        g = DataFlowGraph("test")
        src = DataFlowNode("s", DataFlowNodeKind.CALL_RESULT, "input()", 1)
        src.add_taint(TaintLabel(TaintKind.USER_INPUT))
        b1 = DataFlowNode("b1", DataFlowNodeKind.VARIABLE, "x", 2)
        b2 = DataFlowNode("b2", DataFlowNodeKind.VARIABLE, "y", 3)
        g.add_node(src)
        g.add_node(b1)
        g.add_node(b2)
        g.add_edge(DataFlowEdge("s", "b1", DataFlowEdgeKind.ASSIGNMENT, 2))
        g.add_edge(DataFlowEdge("s", "b2", DataFlowEdgeKind.ASSIGNMENT, 3))
        engine = PropagationEngine(g)
        engine.propagate()
        assert b1.is_tainted()
        assert b2.is_tainted()


# ═══════════════════════════════════════════════════════════════════
# Flow Queries
# ═══════════════════════════════════════════════════════════════════

class TestFlowQueries:
    def _make_graph(self):
        g = DataFlowGraph("test")
        src = DataFlowNode("s", DataFlowNodeKind.CALL_RESULT, "input()", 1)
        src.is_source = True
        src.add_taint(TaintLabel(TaintKind.USER_INPUT))
        mid = DataFlowNode("m", DataFlowNodeKind.VARIABLE, "user_data", 2)
        sink = DataFlowNode("k", DataFlowNodeKind.CALL_RESULT, "eval()", 3)
        sink.is_sink = True
        g.add_node(src)
        g.add_node(mid)
        g.add_node(sink)
        g.add_edge(DataFlowEdge("s", "m", DataFlowEdgeKind.ASSIGNMENT, 2))
        g.add_edge(DataFlowEdge("m", "k", DataFlowEdgeKind.PARAMETER_PASS, 3))
        return g

    def test_get_sources(self):
        g = self._make_graph()
        sources = flow_queries.get_sources(g)
        assert len(sources) == 1

    def test_get_sinks(self):
        g = self._make_graph()
        sinks = flow_queries.get_sinks(g)
        assert len(sinks) == 1

    def test_trace_variable(self):
        g = self._make_graph()
        traced = flow_queries.trace_variable(g, "user_data")
        assert len(traced) >= 1

    def test_trace_function(self):
        g = self._make_graph()
        traced = flow_queries.trace_function(g, "input")
        ids = [n.id for n in traced]
        assert "m" in ids

    def test_trace_to_sink(self):
        g = self._make_graph()
        paths = flow_queries.trace_to_sink(g, "s")
        assert len(paths) >= 1
        assert paths[0].sink_node_id == "k"

    def test_trace_from_source(self):
        g = self._make_graph()
        paths = flow_queries.trace_from_source(g, "k")
        assert len(paths) >= 1
        assert paths[0].source_node_id == "s"

    def test_reachable_sinks(self):
        g = self._make_graph()
        sinks = flow_queries.reachable_sinks(g, "s")
        assert len(sinks) == 1

    def test_reachable_sources(self):
        g = self._make_graph()
        sources = flow_queries.reachable_sources(g, "k")
        assert len(sources) == 1

    def test_has_taint_flow(self):
        g = self._make_graph()
        assert flow_queries.has_taint_flow(g, "s", "k")
        assert not flow_queries.has_taint_flow(g, "k", "s")

    def test_get_data_dependencies(self):
        g = self._make_graph()
        deps = flow_queries.get_data_dependencies(g, "m")
        assert len(deps) == 1
        assert deps[0].id == "s"

    def test_get_reverse_dependencies(self):
        g = self._make_graph()
        rdeps = flow_queries.get_reverse_dependencies(g, "m")
        assert len(rdeps) == 1
        assert rdeps[0].id == "k"

    def test_get_flow_summary(self):
        g = self._make_graph()
        summary = flow_queries.get_flow_summary(g)
        assert summary["total_nodes"] == 3
        assert summary["total_edges"] == 2
        assert summary["sources"] == 1
        assert summary["sinks"] == 1
