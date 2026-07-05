"""
CodeGuard V2 — Data Flow Analysis Layer.

Sub-packages:
    graph/         DataFlowGraph, Builder, Node, Edge
    propagation/   PropagationEngine, AliasTracker, FlowQueries
    taint/         SourceDetector, SinkDetector, TaintEngine, VulnerabilityRules
"""

from app.analysis.dataflow.constants import (
    DataFlowNodeKind,
    DataFlowEdgeKind,
    TaintKind,
    Severity,
)
from app.analysis.dataflow.models import TaintLabel, FlowPath, VulnerabilityFinding
from app.analysis.dataflow.graph import (
    DataFlowNode,
    DataFlowEdge,
    DataFlowGraph,
    DataFlowBuilder,
)
from app.analysis.dataflow.taint import TaintEngine, VulnerabilityRules

__all__ = [
    # constants
    "DataFlowNodeKind",
    "DataFlowEdgeKind",
    "TaintKind",
    "Severity",
    # models
    "TaintLabel",
    "FlowPath",
    "VulnerabilityFinding",
    # graph
    "DataFlowNode",
    "DataFlowEdge",
    "DataFlowGraph",
    "DataFlowBuilder",
    # taint
    "TaintEngine",
    "VulnerabilityRules",
]
