"""
Propagation models — lightweight data containers for propagation chains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.dataflow.constants import DataFlowEdgeKind


@dataclass
class PropagationStep:
    """A single hop in a propagation chain."""
    from_node_id: str
    to_node_id: str
    edge_kind: DataFlowEdgeKind
    line: Optional[int] = None
    scope: Optional[str] = None


@dataclass
class PropagationChain:
    """An ordered sequence of propagation steps from origin to destination."""
    steps: List[PropagationStep] = field(default_factory=list)

    @property
    def origin(self) -> Optional[str]:
        return self.steps[0].from_node_id if self.steps else None

    @property
    def destination(self) -> Optional[str]:
        return self.steps[-1].to_node_id if self.steps else None

    @property
    def length(self) -> int:
        return len(self.steps)

    def node_ids(self) -> List[str]:
        """All unique node IDs visited, in order."""
        if not self.steps:
            return []
        ids = [self.steps[0].from_node_id]
        for step in self.steps:
            ids.append(step.to_node_id)
        return ids
