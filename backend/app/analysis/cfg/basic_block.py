import ast
from typing import List

class BasicBlock:
    """Represents a basic block: a straight-line code sequence with no branches except at the entry/exit."""
    
    def __init__(self, block_id: str):
        self.id: str = block_id
        self.statements: List[ast.AST] = []

    def add_statement(self, stmt: ast.AST) -> None:
        self.statements.append(stmt)

    def is_empty(self) -> bool:
        return len(self.statements) == 0

    def get_label(self) -> str:
        """Returns a string representation of the block's statements."""
        if not self.statements:
            return f"Empty Block {self.id}"
        lines = []
        for stmt in self.statements:
            lineno = getattr(stmt, "lineno", "?")
            lines.append(f"[{lineno}] {type(stmt).__name__}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"BasicBlock(id={self.id}, statements={len(self.statements)})"
