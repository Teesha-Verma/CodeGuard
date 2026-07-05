"""
Data Flow Node — extends the shared GraphNode.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Set

from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_types import NodeKind
from app.analysis.dataflow.constants import DataFlowNodeKind
from app.analysis.dataflow.models import TaintLabel


class DataFlowNode(GraphNode):
    """A node in the Data Flow Graph representing a data element."""

    def __init__(
        self,
        node_id: str,
        df_kind: DataFlowNodeKind,
        name: str,
        line: Optional[int] = None,
        scope: Optional[str] = None,
        file_path: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        merged_props = properties or {}
        merged_props.update({
            "df_kind": df_kind.value,
            "name": name,
            "line": line,
            "scope": scope,
            "file_path": file_path,
        })
        super().__init__(
            node_id=node_id,
            kind=NodeKind.GENERIC,
            label=f"{df_kind.value}:{name}@L{line}",
            properties=merged_props,
        )
        self.df_kind: DataFlowNodeKind = df_kind
        self.name: str = name
        self.line: Optional[int] = line
        self.scope: Optional[str] = scope
        self.file_path: Optional[str] = file_path
        self.taint_labels: Set[TaintLabel] = set()
        self.is_source: bool = False
        self.is_sink: bool = False

    # ── Taint helpers ────────────────────────────────────────────

    def add_taint(self, label: TaintLabel) -> None:
        self.taint_labels.add(label)

    def is_tainted(self) -> bool:
        return len(self.taint_labels) > 0

    def clear_taint(self) -> None:
        self.taint_labels.clear()

    # ── Serialization ────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "df_kind": self.df_kind.value,
            "name": self.name,
            "line": self.line,
            "scope": self.scope,
            "file_path": self.file_path,
            "is_source": self.is_source,
            "is_sink": self.is_sink,
            "is_tainted": self.is_tainted(),
            "taint_labels": [t.kind.value for t in self.taint_labels],
        }

    def __repr__(self) -> str:
        return (
            f"DataFlowNode(id={self.id}, kind={self.df_kind.value}, "
            f"name={self.name}, line={self.line})"
        )
