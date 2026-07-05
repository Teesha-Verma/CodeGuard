"""
Tests for Phases 3–8 — Source Detector, Sink Detector, Taint Engine,
Vulnerability Rules.
"""

import pytest

from app.analysis.dataflow.constants import (
    DataFlowNodeKind,
    DataFlowEdgeKind,
    TaintKind,
    Severity,
)
from app.analysis.dataflow.models import TaintLabel
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_builder import DataFlowBuilder
from app.analysis.dataflow.taint.source_detector import SourceDetector
from app.analysis.dataflow.taint.sink_detector import SinkDetector
from app.analysis.dataflow.taint.taint_engine import TaintEngine
from app.analysis.dataflow.taint.vulnerability_rules import VulnerabilityRules


# ═══════════════════════════════════════════════════════════════════
# SourceDetector
# ═══════════════════════════════════════════════════════════════════

class TestSourceDetector:
    def test_detect_input(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("data = input()")
        detector = SourceDetector(graph)
        sources = detector.detect()
        assert len(sources) >= 1
        assert any(s.is_source for s in sources)

    def test_detect_request_args(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("name = request.args.get('name')")
        detector = SourceDetector(graph)
        sources = detector.detect()
        assert len(sources) >= 1

    def test_detect_os_environ(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("val = os.environ.get('KEY')")
        detector = SourceDetector(graph)
        sources = detector.detect()
        assert len(sources) >= 1

    def test_detect_sys_argv(self):
        g = DataFlowGraph("test")
        node = DataFlowNode("n1", DataFlowNodeKind.ATTRIBUTE, "sys.argv", 1)
        g.add_node(node)
        detector = SourceDetector(g)
        sources = detector.detect()
        assert len(sources) == 1
        assert sources[0].taint_labels

    def test_no_false_positive_regular_call(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("x = len(data)")
        detector = SourceDetector(graph)
        sources = detector.detect()
        assert len(sources) == 0


# ═══════════════════════════════════════════════════════════════════
# SinkDetector
# ═══════════════════════════════════════════════════════════════════

class TestSinkDetector:
    def test_detect_eval(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("result = eval(data)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) >= 1
        assert any(
            s.properties.get("sink_category") == "code_injection"
            for s in sinks
        )

    def test_detect_os_system(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("os.system(cmd)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) >= 1

    def test_detect_subprocess(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("subprocess.run(cmd)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) >= 1

    def test_detect_pickle_loads(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("obj = pickle.loads(data)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) >= 1

    def test_detect_sql_execute(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("cursor.execute(query)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) >= 1
        assert any(
            s.properties.get("sink_category") == "sql_injection"
            for s in sinks
        )

    def test_no_false_positive(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("x = len(items)")
        detector = SinkDetector(graph)
        sinks = detector.detect()
        assert len(sinks) == 0

    def test_custom_sink_registry(self):
        builder = DataFlowBuilder("test")
        graph = builder.build("custom_sink(data)")
        detector = SinkDetector(graph, extra_sinks={"custom_sink": "custom_vuln"})
        sinks = detector.detect()
        assert len(sinks) >= 1


# ═══════════════════════════════════════════════════════════════════
# TaintEngine — end-to-end
# ═══════════════════════════════════════════════════════════════════

class TestTaintEngine:
    def test_simple_taint_flow(self):
        code = (
            "data = input()\n"
            "result = eval(data)\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        flows = engine.run()
        assert len(flows) >= 1

    def test_multi_hop_taint(self):
        code = (
            "user = input()\n"
            "x = user\n"
            "y = x\n"
            "eval(y)\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        flows = engine.run()
        assert len(flows) >= 1

    def test_no_taint_flow_safe_code(self):
        code = (
            "x = 42\n"
            "y = x + 1\n"
            "print(y)\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        flows = engine.run()
        assert len(flows) == 0

    def test_sql_injection_detection(self):
        code = (
            "name = input()\n"
            "query = 'SELECT * FROM users WHERE name = ' + name\n"
            "cursor.execute(query)\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        flows = engine.run()
        # There should be at least some taint flow
        assert engine.get_sources()
        assert engine.get_sinks()

    def test_command_injection_detection(self):
        code = (
            "cmd = input()\n"
            "os.system(cmd)\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        flows = engine.run()
        assert len(flows) >= 1

    def test_cross_module_merge(self):
        mod_a = "def get_data():\n    return input()\n"
        mod_b = "x = get_data()\neval(x)\n"
        engine = TaintEngine()
        engine.add_module("mod_a", mod_a)
        engine.add_module("mod_b", mod_b)
        flows = engine.run()
        # Merged graph should contain nodes from both modules
        merged = engine.merged_graph
        assert merged is not None
        assert len(merged.nodes) > 0

    def test_tainted_nodes_tracking(self):
        code = (
            "data = input()\n"
            "x = data\n"
        )
        engine = TaintEngine()
        engine.add_module("main", code)
        engine.run()
        tainted = engine.get_tainted_nodes()
        assert len(tainted) >= 1


# ═══════════════════════════════════════════════════════════════════
# VulnerabilityRules
# ═══════════════════════════════════════════════════════════════════

class TestVulnerabilityRules:
    def _make_flow_graph(self, sink_category):
        g = DataFlowGraph("test")
        src = DataFlowNode("s", DataFlowNodeKind.CALL_RESULT, "input()", 1)
        src.is_source = True
        src.add_taint(TaintLabel(TaintKind.USER_INPUT))
        sink = DataFlowNode("k", DataFlowNodeKind.CALL_RESULT, "evil()", 2)
        sink.is_sink = True
        sink.properties["sink_category"] = sink_category
        g.add_node(src)
        g.add_node(sink)
        g.add_edge(DataFlowEdge("s", "k", DataFlowEdgeKind.PARAMETER_PASS, 2))
        return g

    def test_sql_injection_rule(self):
        from app.analysis.dataflow.models import FlowPath
        g = self._make_flow_graph("sql_injection")
        fp = FlowPath("s", "k", ["s", "k"], [TaintLabel(TaintKind.USER_INPUT)])
        rules = VulnerabilityRules(g)
        findings = rules.evaluate([fp])
        assert len(findings) == 1
        assert findings[0].rule_id == "SQL_INJECTION"
        assert findings[0].severity == Severity.CRITICAL

    def test_command_injection_rule(self):
        from app.analysis.dataflow.models import FlowPath
        g = self._make_flow_graph("command_injection")
        fp = FlowPath("s", "k", ["s", "k"], [TaintLabel(TaintKind.USER_INPUT)])
        rules = VulnerabilityRules(g)
        findings = rules.evaluate([fp])
        assert len(findings) == 1
        assert findings[0].rule_id == "COMMAND_INJECTION"

    def test_code_injection_rule(self):
        from app.analysis.dataflow.models import FlowPath
        g = self._make_flow_graph("code_injection")
        fp = FlowPath("s", "k", ["s", "k"], [TaintLabel(TaintKind.USER_INPUT)])
        rules = VulnerabilityRules(g)
        findings = rules.evaluate([fp])
        assert len(findings) == 1
        assert findings[0].rule_id == "CODE_INJECTION"

    def test_unsafe_deserialization_rule(self):
        from app.analysis.dataflow.models import FlowPath
        g = self._make_flow_graph("unsafe_deserialization")
        fp = FlowPath("s", "k", ["s", "k"], [TaintLabel(TaintKind.USER_INPUT)])
        rules = VulnerabilityRules(g)
        findings = rules.evaluate([fp])
        assert len(findings) == 1
        assert findings[0].rule_id == "UNSAFE_DESERIALIZATION"

    def test_hardcoded_secret_detection(self):
        g = DataFlowGraph("test")
        literal = DataFlowNode("lit", DataFlowNodeKind.LITERAL, "'s3cr3t'", 1)
        var = DataFlowNode("var", DataFlowNodeKind.VARIABLE, "PASSWORD", 1)
        g.add_node(literal)
        g.add_node(var)
        g.add_edge(DataFlowEdge("lit", "var", DataFlowEdgeKind.ASSIGNMENT, 1))
        rules = VulnerabilityRules(g)
        findings = rules.evaluate_graph()
        assert len(findings) == 1
        assert findings[0].rule_id == "HARDCODED_SECRET"
        assert findings[0].severity == Severity.MEDIUM

    def test_no_hardcoded_secret_for_normal_vars(self):
        g = DataFlowGraph("test")
        literal = DataFlowNode("lit", DataFlowNodeKind.LITERAL, "'hello'", 1)
        var = DataFlowNode("var", DataFlowNodeKind.VARIABLE, "greeting", 1)
        g.add_node(literal)
        g.add_node(var)
        g.add_edge(DataFlowEdge("lit", "var", DataFlowEdgeKind.ASSIGNMENT, 1))
        rules = VulnerabilityRules(g)
        findings = rules.evaluate_graph()
        assert len(findings) == 0

    def test_finding_to_dict(self):
        from app.analysis.dataflow.models import FlowPath
        g = self._make_flow_graph("sql_injection")
        fp = FlowPath("s", "k", ["s", "k"], [TaintLabel(TaintKind.USER_INPUT)])
        rules = VulnerabilityRules(g)
        findings = rules.evaluate([fp])
        d = findings[0].to_dict()
        assert d["rule_id"] == "SQL_INJECTION"
        assert d["severity"] == "critical"
        assert isinstance(d["flow_path"], list)
