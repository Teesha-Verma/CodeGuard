from typing import Dict, Any, Optional
from app.analysis.graph.graph_types import NodeKind

class GraphNode:
    """Represents a generic node in the graph structure."""
    
    def __init__(
        self,
        node_id: str,
        kind: NodeKind = NodeKind.GENERIC,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        self.id: str = node_id
        self.kind: NodeKind = kind
        self.label: Optional[str] = label or node_id
        self.properties: Dict[str, Any] = properties or {}

    def __repr__(self) -> str:
        return f"GraphNode(id={self.id}, kind={self.kind}, label={self.label})"
