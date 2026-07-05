"""
Tests for Phase 1 — Data Flow Graph Infrastructure.

Covers: DataFlowNode, DataFlowEdge, DataFlowGraph, DataFlowBuilder.
"""

import ast
import pytest

from app.analysis.dataflow.constants import (
    DataFlowNodeKind,
    DataFlowEdgeKind,
    TaintKind,
    Severity,
)
from app.analysis.dataflow.models import TaintLabel, FlowPath, VulnerabilityFinding
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_builder import DataFlowBuilder


# ═══════════════════════════════════════════════════════════════════
# DataFlowNode
# ═══════════════════════════════════════════════════════════════════

class TestDataFlowNode:
    def test_create_basic_node(self):
        node = DataFlowNode(
            node_id="n1",
            df_kind=DataFlowNodeKind.VARIABLE,
            name="x",
            line=10,
            scope="main",
        )
        assert node.id == "n1"
        assert node.df_kind == DataFlowNodeKind.VARIABLE
        assert node.name == "x"
        assert node.line == 10
        assert node.scope == "main"
        assert not node.is_source
        assert not node.is_sink
        assert not node.is_tainted()

    def test_taint_operations(self):
        node = DataFlowNode("n1", DataFlowNodeKind.VARIABLE, "x", 1)
        label = TaintLabel(kind=TaintKind.USER_INPUT, source_name="input()")
        node.add_taint(label)
        assert node.is_tainted()
        assert len(node.taint_labels) == 1

        # duplicate label is not added
        node.add_taint(label)
        assert len(node.taint_labels) == 1

        node.clear_taint()
        assert not node.is_tainted()

    def test_to_dict(self):
        node = DataFlowNode("n1", DataFlowNodeKind.PARAMETER, "arg1", 5)
        d = node.to_dict()
        assert d["id"] == "n1"
        assert d["df_kind"] == "df_parameter"
        assert d["name"] == "arg1"
        assert d["line"] == 5
        assert d["is_tainted"] is False


# ═══════════════════════════════════════════════════════════════════
# DataFlowEdge
# ═══════════════════════════════════════════════════════════════════

class TestDataFlowEdge:
    def test_create_edge(self):
        edge = DataFlowEdge(
            source="n1",
            target="n2",
            df_kind=DataFlowEdgeKind.ASSIGNMENT,
            line=10,
        )
        assert edge.source == "n1"
        assert edge.target == "n2"
        assert edge.df_kind == DataFlowEdgeKind.ASSIGNMENT
        assert edge.line == 10

    def test_to_dict(self):
        edge = DataFlowEdge("a", "b", DataFlowEdgeKind.PARAMETER_PASS, 7)
        d = edge.to_dict()
        assert d["source"] == "a"
        assert d["target"] == "b"
        assert d["df_kind"] == "df_parameter_pass"


# ═══════════════════════════════════════════════════════════════════
# DataFlowGraph
# ═══════════════════════════════════════════════════════════════════

class TestDataFlowGraph:
    def _make_graph(self):
        g = DataFlowGraph(module_name="test")
        n1 = DataFlowNode("n1", DataFlowNodeKind.VARIABLE, "x", 1)
        n2 = DataFlowNode("n2", DataFlowNodeKind.VARIABLE, "y", 2)
        n3 = DataFlowNode("n3", DataFlowNodeKind.VARIABLE, "z", 3)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)
        g.add_edge(DataFlowEdge("n1", "n2", DataFlowEdgeKind.ASSIGNMENT, 2))
        g.add_edge(DataFlowEdge("n2", "n3", DataFlowEdgeKind.ASSIGNMENT, 3))
        return g

    def test_reachable_nodes(self):
        g = self._make_graph()
        reachable = g.reachable_nodes("n1")
        assert "n2" in reachable
        assert "n3" in reachable
        assert "n1" not in reachable

    def test_trace_flow(self):
        g = self._make_graph()
        flow = g.trace_flow("n1")
        names = [n.name for n in flow]
        assert "y" in names
        assert "z" in names

    def test_find_flow_between(self):
        g = self._make_graph()
        path = g.find_flow_between("n1", "n3")
        assert path is not None
        assert path == ["n1", "n2", "n3"]

    def test_find_flow_between_no_path(self):
        g = self._make_graph()
        path = g.find_flow_between("n3", "n1")
        assert path is None

    def test_get_sources_sinks(self):
        g = self._make_graph()
        n1 = g.get_df_node("n1")
        n3 = g.get_df_node("n3")
        n1.is_source = True
        n3.is_sink = True
        assert len(g.get_sources()) == 1
        assert len(g.get_sinks()) == 1

    def test_get_nodes_by_name(self):
        g = self._make_graph()
        nodes = g.get_nodes_by_name("x")
        assert len(nodes) == 1
        assert nodes[0].id == "n1"

    def test_to_dict(self):
        g = self._make_graph()
        d = g.to_dict()
        assert d["module_name"] == "test"
        assert d["node_count"] == 3
        assert d["edge_count"] == 2

    def test_inherited_bfs_dfs(self):
        """Verify inherited traversal from Graph base works."""
        g = self._make_graph()
        bfs_nodes = list(g.bfs("n1"))
        assert len(bfs_nodes) == 3
        dfs_nodes = list(g.dfs("n1"))
        assert len(dfs_nodes) == 3

    def test_inherited_has_cycle(self):
        g = self._make_graph()
        assert not g.has_cycle()
        # Add a back-edge
        g.add_edge(DataFlowEdge("n3", "n1", DataFlowEdgeKind.ALIAS))
        assert g.has_cycle()


# ═══════════════════════════════════════════════════════════════════
# DataFlowBuilder
# ═══════════════════════════════════════════════════════════════════

class TestDataFlowBuilder:
    def test_simple_assignment(self):
        code = "x = 42\ny = x\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        # x should appear as a variable
        var_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)
        var_names = [n.name for n in var_nodes]
        assert "x" in var_names
        assert "y" in var_names

    def test_augmented_assign(self):
        code = "x = 0\nx += 1\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        aug_edges = graph.get_edges_by_kind(DataFlowEdgeKind.AUGMENTED_ASSIGN)
        assert len(aug_edges) >= 1

    def test_tuple_unpacking(self):
        code = "a, b = 1, 2\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        var_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)
        var_names = [n.name for n in var_nodes]
        assert "a" in var_names
        assert "b" in var_names
        unpack_edges = graph.get_edges_by_kind(DataFlowEdgeKind.TUPLE_UNPACK)
        assert len(unpack_edges) >= 1

    def test_function_params(self):
        code = "def foo(x, y):\n    return x + y\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        params = graph.get_nodes_by_kind(DataFlowNodeKind.PARAMETER)
        param_names = [p.name for p in params]
        assert "x" in param_names
        assert "y" in param_names

    def test_return_value(self):
        code = "def foo():\n    return 42\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        ret_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.RETURN_VALUE)
        assert len(ret_nodes) >= 1
        ret_edges = graph.get_edges_by_kind(DataFlowEdgeKind.RETURN_PROPAGATION)
        assert len(ret_edges) >= 1

    def test_function_call(self):
        code = "result = foo(x)\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        call_results = graph.get_nodes_by_kind(DataFlowNodeKind.CALL_RESULT)
        assert len(call_results) >= 1
        func_args = graph.get_nodes_by_kind(DataFlowNodeKind.FUNCTION_ARG)
        assert len(func_args) >= 1

    def test_attribute_write(self):
        code = "self.name = value\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        attr_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.ATTRIBUTE)
        assert len(attr_nodes) >= 1
        attr_edges = graph.get_edges_by_kind(DataFlowEdgeKind.ATTRIBUTE_WRITE)
        assert len(attr_edges) >= 1

    def test_subscript_write(self):
        code = "data[key] = value\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        coll_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.COLLECTION_ELEMENT)
        assert len(coll_nodes) >= 1

    def test_import_tracking(self):
        code = "import os\nfrom sys import argv\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        imports = graph.get_nodes_by_kind(DataFlowNodeKind.IMPORT)
        assert len(imports) >= 2

    def test_for_loop(self):
        code = "for item in items:\n    x = item\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        var_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)
        var_names = [n.name for n in var_nodes]
        assert "item" in var_names
        assert "x" in var_names

    def test_with_statement(self):
        code = "with open('file') as f:\n    data = f.read()\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        var_names = [n.name for n in graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)]
        assert "f" in var_names

    def test_class_methods(self):
        code = (
            "class MyClass:\n"
            "    def method(self, x):\n"
            "        self.x = x\n"
        )
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        params = graph.get_nodes_by_kind(DataFlowNodeKind.PARAMETER)
        param_names = [p.name for p in params]
        assert "self" in param_names
        assert "x" in param_names

    def test_chained_assignment(self):
        code = "a = b = c = 42\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        var_nodes = graph.get_nodes_by_kind(DataFlowNodeKind.VARIABLE)
        var_names = [n.name for n in var_nodes]
        assert "a" in var_names
        assert "b" in var_names
        assert "c" in var_names

    def test_build_from_tree(self):
        code = "x = 1\n"
        tree = ast.parse(code)
        builder = DataFlowBuilder("test_mod")
        graph = builder.build_from_tree(tree)
        assert len(graph.nodes) > 0

    def test_syntax_error_returns_empty_graph(self):
        builder = DataFlowBuilder("test_mod")
        graph = builder.build("def {invalid syntax")
        assert len(graph.nodes) == 0

    def test_serialization(self):
        code = "x = input()\ny = x\n"
        builder = DataFlowBuilder("test_mod")
        graph = builder.build(code)
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert d["node_count"] > 0


# ═══════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════

class TestModels:
    def test_taint_label_hash_equality(self):
        t1 = TaintLabel(TaintKind.USER_INPUT, source_name="input()")
        t2 = TaintLabel(TaintKind.USER_INPUT, source_name="input()")
        assert t1 == t2
        assert hash(t1) == hash(t2)

    def test_flow_path_length(self):
        fp = FlowPath("s1", "s2", ["s1", "n1", "s2"])
        assert fp.length == 3

    def test_vulnerability_finding_to_dict(self):
        fp = FlowPath("s1", "s2", ["s1", "s2"])
        vf = VulnerabilityFinding(
            rule_id="SQL_INJECTION",
            title="SQL Injection",
            severity=Severity.CRITICAL,
            description="test",
            source_node_id="s1",
            sink_node_id="s2",
            flow_path=fp,
        )
        d = vf.to_dict()
        assert d["rule_id"] == "SQL_INJECTION"
        assert d["severity"] == "critical"
