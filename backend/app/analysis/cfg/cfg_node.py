from typing import Optional
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_types import NodeKind
from app.analysis.cfg.basic_block import BasicBlock

class CFGNode(GraphNode):
    """Subclass of GraphNode specifically representing a node in a Control Flow Graph."""
    
    def __init__(
        self,
        node_id: str,
        kind: NodeKind = NodeKind.CFG_STATEMENT,
        label: Optional[str] = None,
        block: Optional[BasicBlock] = None
    ):
        super().__init__(node_id=node_id, kind=kind, label=label)
        self.block: Optional[BasicBlock] = block
        
        # If block is provided and no label is specified, use block's label
        if block and not label:
            self.label = block.get_label()

    def __repr__(self) -> str:
        return f"CFGNode(id={self.id}, kind={self.kind}, label={self.label})"
