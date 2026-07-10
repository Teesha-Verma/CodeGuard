from app.analysis.graph.graph_base import Graph
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_edge import GraphEdge
from app.analysis.graph.graph_types import NodeKind, EdgeKind
from typing import Optional

class CallGraphNode(GraphNode):
    """Represents a function or method definition node in the Call Graph."""
    
    def __init__(
        self,
        node_id: str,
        kind: NodeKind = NodeKind.CALL_FUNCTION,
        label: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ):
        properties = {
            "file_path": file_path,
            "line_number": line_number
        }
        super().__init__(node_id=node_id, kind=kind, label=label, properties=properties)

    @property
    def file_path(self) -> Optional[str]:
        return self.properties.get("file_path")

    @property
    def line_number(self) -> Optional[int]:
        return self.properties.get("line_number")


class CallGraphEdge(GraphEdge):
    """Represents a call edge (caller -> callee) in the Call Graph."""
    
    def __init__(
        self,
        source: str,
        target: str,
        call_site_line: Optional[int] = None
    ):
        properties = {"call_site_line": call_site_line}
        super().__init__(source=source, target=target, kind=EdgeKind.CALL, label="CALLS", properties=properties)

    @property
    def call_site_line(self) -> Optional[int]:
        return self.properties.get("call_site_line")


class CallGraph(Graph):
    """Represents the global Call Graph for a repository."""
    
    def __init__(self):
        super().__init__()
