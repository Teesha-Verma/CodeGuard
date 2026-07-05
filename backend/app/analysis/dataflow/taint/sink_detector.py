"""
Sink Detector — deterministic detection of dangerous sinks.

Scans DataFlowGraph nodes for calls / attributes that represent
security-sensitive operations (eval, exec, SQL execute, subprocess, etc.)
and marks them as sinks.

Supports a configurable sink registry.
"""

from __future__ import annotations

import re
from typing import List, Dict, Optional

from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.constants import DataFlowNodeKind


# ── Default sink registry ────────────────────────────────────────

_DEFAULT_SINKS: Dict[str, str] = {
    # function pattern → vulnerability category
    "eval": "code_injection",
    "exec": "code_injection",
    "compile": "code_injection",
    "os.system": "command_injection",
    "os.popen": "command_injection",
    "subprocess.run": "command_injection",
    "subprocess.call": "command_injection",
    "subprocess.check_call": "command_injection",
    "subprocess.check_output": "command_injection",
    "subprocess.Popen": "command_injection",
    "pickle.loads": "unsafe_deserialization",
    "pickle.load": "unsafe_deserialization",
    "cPickle.loads": "unsafe_deserialization",
    "cPickle.load": "unsafe_deserialization",
    "marshal.loads": "unsafe_deserialization",
    "marshal.load": "unsafe_deserialization",
    "shelve.open": "unsafe_deserialization",
    "yaml.load": "unsafe_yaml",
    "yaml.unsafe_load": "unsafe_yaml",
    "cursor.execute": "sql_injection",
    "cursor.executemany": "sql_injection",
    "connection.execute": "sql_injection",
    "sqlite3.execute": "sql_injection",
    "db.execute": "sql_injection",
    "open": "unsafe_file_access",
    "io.open": "unsafe_file_access",
    "requests.get": "ssrf",
    "requests.post": "ssrf",
    "requests.put": "ssrf",
    "requests.delete": "ssrf",
    "requests.request": "ssrf",
    "urllib.request.urlopen": "ssrf",
    "httpx.get": "ssrf",
    "httpx.post": "ssrf",
}

# Regex patterns for sinks that need prefix matching
_SINK_PATTERNS = [
    (re.compile(r"^cursor\.execute"), "sql_injection"),
    (re.compile(r"^conn\.execute"), "sql_injection"),
    (re.compile(r"^db\.execute"), "sql_injection"),
    (re.compile(r"^session\.execute"), "sql_injection"),
    (re.compile(r"^subprocess\.\w+"), "command_injection"),
    (re.compile(r"^os\.exec\w*"), "command_injection"),
    (re.compile(r"^os\.spawn\w*"), "command_injection"),
]


class SinkDetector:
    """Detects and marks sink nodes in a DataFlowGraph."""

    def __init__(
        self,
        graph: DataFlowGraph,
        extra_sinks: Optional[Dict[str, str]] = None,
    ):
        self.graph = graph
        self.sink_registry: Dict[str, str] = dict(_DEFAULT_SINKS)
        if extra_sinks:
            self.sink_registry.update(extra_sinks)

    def detect(self) -> List[DataFlowNode]:
        """Scan all nodes and mark sinks. Returns newly-marked sink nodes."""
        sinks: List[DataFlowNode] = []
        for node in self.graph.get_df_nodes():
            category = self._match_sink(node)
            if category is not None:
                node.is_sink = True
                node.properties["sink_category"] = category
                sinks.append(node)
        return sinks

    def _match_sink(self, node: DataFlowNode) -> Optional[str]:
        # Only call-result and function-arg nodes can be sinks
        if node.df_kind not in (
            DataFlowNodeKind.CALL_RESULT,
            DataFlowNodeKind.FUNCTION_ARG,
        ):
            return None

        name = node.name.rstrip("()")

        # exact match in registry
        if name in self.sink_registry:
            return self.sink_registry[name]

        # regex patterns
        for pattern, category in _SINK_PATTERNS:
            if pattern.search(name):
                return category

        # check if the node name contains a known sink as a suffix
        # e.g. "db.cursor.execute" should match "cursor.execute"
        for sink_name, category in self.sink_registry.items():
            if name.endswith(sink_name):
                return category

        return None
