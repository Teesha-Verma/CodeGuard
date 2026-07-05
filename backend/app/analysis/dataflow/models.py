"""
Data Flow Analysis — Shared data models.

Lightweight dataclasses used across the data flow, propagation,
and taint subsystems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from app.analysis.dataflow.constants import TaintKind, Severity


@dataclass
class TaintLabel:
    """A taint annotation attached to a data-flow node."""
    kind: TaintKind
    source_line: Optional[int] = None
    source_name: Optional[str] = None
    description: str = ""

    def __hash__(self) -> int:
        return hash((self.kind, self.source_line, self.source_name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaintLabel):
            return NotImplemented
        return (self.kind == other.kind
                and self.source_line == other.source_line
                and self.source_name == other.source_name)


@dataclass
class FlowPath:
    """A concrete path from a source node to a sink node."""
    source_node_id: str
    sink_node_id: str
    path_node_ids: List[str] = field(default_factory=list)
    taint_labels: List[TaintLabel] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.path_node_ids)


@dataclass
class VulnerabilityFinding:
    """A deterministic vulnerability detected by the taint engine."""
    rule_id: str
    title: str
    severity: Severity
    description: str
    source_node_id: str
    sink_node_id: str
    flow_path: FlowPath
    source_line: Optional[int] = None
    sink_line: Optional[int] = None
    source_file: Optional[str] = None
    sink_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "description": self.description,
            "source_node_id": self.source_node_id,
            "sink_node_id": self.sink_node_id,
            "source_line": self.source_line,
            "sink_line": self.sink_line,
            "source_file": self.source_file,
            "sink_file": self.sink_file,
            "flow_path_length": self.flow_path.length,
            "flow_path": self.flow_path.path_node_ids,
            "metadata": self.metadata,
        }
