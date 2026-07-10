from typing import Optional
from app.analysis.graph.graph_edge import GraphEdge
from app.analysis.graph.graph_types import EdgeKind

class CFGEdge(GraphEdge):
    """Subclass of GraphEdge representing a flow edge in a Control Flow Graph."""
    
    def __init__(
        self,
        source: str,
        target: str,
        kind: EdgeKind = EdgeKind.CFG_NORMAL,
        label: Optional[str] = None
    ):
        super().__init__(source=source, target=target, kind=kind, label=label)

    def __repr__(self) -> str:
        return f"CFGEdge(source={self.source}, target={self.target}, kind={self.kind}, label={self.label})"
