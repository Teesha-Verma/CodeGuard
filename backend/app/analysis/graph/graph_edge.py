from typing import Dict, Any, Optional
from app.analysis.graph.graph_types import EdgeKind

class GraphEdge:
    """Represents a directed edge between two nodes in the graph."""
    
    def __init__(
        self,
        source: str,
        target: str,
        kind: EdgeKind = EdgeKind.GENERIC,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        self.source: str = source
        self.target: str = target
        self.kind: EdgeKind = kind
        self.label: Optional[str] = label
        self.properties: Dict[str, Any] = properties or {}

    def __repr__(self) -> str:
        return f"GraphEdge(source={self.source}, target={self.target}, kind={self.kind}, label={self.label})"
