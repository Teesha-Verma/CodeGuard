"""
Source Detector — deterministic detection of taint sources in a DataFlowGraph.

Scans nodes for patterns that introduce untrusted / external data
(user input, HTTP parameters, environment variables, CLI args, etc.)
and marks them as sources with the appropriate TaintLabel.
"""

from __future__ import annotations

import re
from typing import List, Set

from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.constants import DataFlowNodeKind, TaintKind
from app.analysis.dataflow.models import TaintLabel


# ── Source patterns ──────────────────────────────────────────────

_CALL_SOURCES = {
    # function-name pattern → TaintKind
    "input": TaintKind.USER_INPUT,
    "raw_input": TaintKind.USER_INPUT,
    "sys.stdin.read": TaintKind.USER_INPUT,
    "sys.stdin.readline": TaintKind.USER_INPUT,
    "socket.recv": TaintKind.NETWORK_INPUT,
    "socket.recvfrom": TaintKind.NETWORK_INPUT,
    "socket.recvmsg": TaintKind.NETWORK_INPUT,
}

_ATTR_SOURCES = {
    # attribute pattern → TaintKind
    "request.args": TaintKind.HTTP_PARAMETER,
    "request.form": TaintKind.HTTP_PARAMETER,
    "request.json": TaintKind.HTTP_PARAMETER,
    "request.data": TaintKind.HTTP_PARAMETER,
    "request.values": TaintKind.HTTP_PARAMETER,
    "request.headers": TaintKind.HTTP_PARAMETER,
    "request.cookies": TaintKind.HTTP_PARAMETER,
    "request.files": TaintKind.HTTP_PARAMETER,
    "request.query_string": TaintKind.HTTP_PARAMETER,
    "request.GET": TaintKind.HTTP_PARAMETER,
    "request.POST": TaintKind.HTTP_PARAMETER,
    "request.body": TaintKind.HTTP_PARAMETER,
    "request.content": TaintKind.HTTP_PARAMETER,
    "os.environ": TaintKind.ENVIRONMENT,
    "sys.argv": TaintKind.CLI_ARGUMENT,
}

_ATTR_SOURCE_PREFIXES = [
    ("request.args", TaintKind.HTTP_PARAMETER),
    ("request.form", TaintKind.HTTP_PARAMETER),
    ("request.json", TaintKind.HTTP_PARAMETER),
    ("request.headers", TaintKind.HTTP_PARAMETER),
    ("request.cookies", TaintKind.HTTP_PARAMETER),
    ("request.GET", TaintKind.HTTP_PARAMETER),
    ("request.POST", TaintKind.HTTP_PARAMETER),
    ("os.environ", TaintKind.ENVIRONMENT),
]

# Patterns that match call results like request.args.get(...)
_CALL_RESULT_SOURCE_PATTERNS = [
    (re.compile(r"^request\.\w+\.get\b"), TaintKind.HTTP_PARAMETER),
    (re.compile(r"^request\.\w+\["), TaintKind.HTTP_PARAMETER),
    (re.compile(r"^os\.environ\.get\b"), TaintKind.ENVIRONMENT),
    (re.compile(r"^os\.environ\["), TaintKind.ENVIRONMENT),
    (re.compile(r"^os\.getenv\b"), TaintKind.ENVIRONMENT),
    (re.compile(r"^input\b"), TaintKind.USER_INPUT),
    (re.compile(r"^raw_input\b"), TaintKind.USER_INPUT),
    (re.compile(r"^sys\.stdin"), TaintKind.USER_INPUT),
    (re.compile(r"^socket\.recv"), TaintKind.NETWORK_INPUT),
]


class SourceDetector:
    """Detects and marks taint source nodes in a DataFlowGraph."""

    def __init__(self, graph: DataFlowGraph):
        self.graph = graph

    def detect(self) -> List[DataFlowNode]:
        """Scan all nodes and mark sources. Returns newly-marked source nodes."""
        sources: List[DataFlowNode] = []
        for node in self.graph.get_df_nodes():
            label = self._match_source(node)
            if label is not None:
                node.is_source = True
                node.add_taint(label)
                sources.append(node)
        return sources

    def _match_source(self, node: DataFlowNode) -> TaintLabel | None:
        name = node.name

        # Direct call sources: input(), sys.stdin.read(), etc.
        if node.df_kind == DataFlowNodeKind.CALL_RESULT:
            # strip trailing "()" for matching
            func_name = name.rstrip("()")
            if func_name in _CALL_SOURCES:
                return TaintLabel(
                    kind=_CALL_SOURCES[func_name],
                    source_line=node.line,
                    source_name=func_name,
                    description=f"Taint source: call to {func_name}",
                )
            # regex patterns
            for pattern, kind in _CALL_RESULT_SOURCE_PATTERNS:
                if pattern.search(func_name):
                    return TaintLabel(
                        kind=kind,
                        source_line=node.line,
                        source_name=func_name,
                        description=f"Taint source: {func_name}",
                    )

        # Attribute sources: request.args, os.environ, sys.argv
        if node.df_kind in (
            DataFlowNodeKind.ATTRIBUTE,
            DataFlowNodeKind.VARIABLE,
            DataFlowNodeKind.COLLECTION_ELEMENT,
        ):
            if name in _ATTR_SOURCES:
                return TaintLabel(
                    kind=_ATTR_SOURCES[name],
                    source_line=node.line,
                    source_name=name,
                    description=f"Taint source: {name}",
                )
            for prefix, kind in _ATTR_SOURCE_PREFIXES:
                if name.startswith(prefix):
                    return TaintLabel(
                        kind=kind,
                        source_line=node.line,
                        source_name=name,
                        description=f"Taint source: {name}",
                    )

        # Function-arg nodes that themselves carry source patterns
        if node.df_kind == DataFlowNodeKind.FUNCTION_ARG:
            for pattern, kind in _CALL_RESULT_SOURCE_PATTERNS:
                if pattern.search(name):
                    return TaintLabel(
                        kind=kind,
                        source_line=node.line,
                        source_name=name,
                        description=f"Taint source via arg: {name}",
                    )

        return None
