"""
Data Flow Edge — extends the shared GraphEdge.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from app.analysis.graph.graph_edge import GraphEdge
from app.analysis.graph.graph_types import EdgeKind
from app.analysis.dataflow.constants import DataFlowEdgeKind


class DataFlowEdge(GraphEdge):
    """A directed edge in the Data Flow Graph representing data movement."""

    def __init__(
        self,
        source: str,
        target: str,
        df_kind: DataFlowEdgeKind,
        line: Optional[int] = None,
        scope: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        merged_props = properties or {}
        merged_props.update({
            "df_kind": df_kind.value,
            "line": line,
            "scope": scope,
        })
        super().__init__(
            source=source,
            target=target,
            kind=EdgeKind.GENERIC,
            label=df_kind.value,
            properties=merged_props,
        )
        self.df_kind: DataFlowEdgeKind = df_kind
        self.line: Optional[int] = line
        self.scope: Optional[str] = scope

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "df_kind": self.df_kind.value,
            "line": self.line,
            "scope": self.scope,
        }

    def __repr__(self) -> str:
        return (
            f"DataFlowEdge(src={self.source}, tgt={self.target}, "
            f"kind={self.df_kind.value}, line={self.line})"
        )
