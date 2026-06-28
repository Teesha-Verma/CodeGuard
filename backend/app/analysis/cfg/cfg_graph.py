from typing import List, Optional
from app.analysis.graph.graph_base import Graph
from app.analysis.graph.graph_types import NodeKind
from app.analysis.cfg.cfg_node import CFGNode
import ast

class CFGGraph(Graph):
    """Control Flow Graph for a single function or module."""
    
    def __init__(self, function_name: str):
        super().__init__()
        self.function_name: str = function_name
        self.entry_node: Optional[CFGNode] = None
        self.exit_node: Optional[CFGNode] = None

    def find_unreachable_code(self) -> List[CFGNode]:
        """Returns all nodes in the CFG that are unreachable from the entry node."""
        if not self.entry_node:
            return []
            
        reachable_ids = {node.id for node in self.bfs(self.entry_node.id)}
        unreachable = []
        for node_id, node in self.nodes.items():
            if isinstance(node, CFGNode) and node_id not in reachable_ids:
                unreachable.append(node)
        return unreachable

    def find_missing_return_paths(self) -> List[CFGNode]:
        """
        Returns basic blocks that fall through to the exit node (implicit return None)
        when the function contains at least one explicit return statement with a value.
        """
        # 1. Check if the function has at least one return statement with a value
        has_explicit_return_value = False
        for node_id, node in self.nodes.items():
            if isinstance(node, CFGNode) and node.block:
                for stmt in node.block.statements:
                    if isinstance(stmt, ast.Return) and stmt.value is not None:
                        has_explicit_return_value = True
                        break
            if has_explicit_return_value:
                break

        if not has_explicit_return_value:
            return []

        # 2. Find blocks that are reachable from entry, and connect to the exit node
        # but do NOT end with an explicit Return or Raise statement.
        missing_return_blocks = []
        if not self.entry_node or not self.exit_node:
            return []

        reachable_nodes = list(self.bfs(self.entry_node.id))
        for node in reachable_nodes:
            if node.id == self.exit_node.id or node.id == self.entry_node.id:
                continue
            
            successors = self.get_successors(node.id)
            is_terminal = len(successors) == 0 or (len(successors) == 1 and successors[0].id == self.exit_node.id)
            
            if is_terminal and isinstance(node, CFGNode) and node.block:
                has_return_or_raise = False
                if node.block.statements:
                    last_stmt = node.block.statements[-1]
                    if isinstance(last_stmt, (ast.Return, ast.Raise)):
                        has_return_or_raise = True
                
                if not has_return_or_raise:
                    missing_return_blocks.append(node)

        return missing_return_blocks

    def find_dead_branches(self) -> List[CFGNode]:
        """
        Detects if-statements or loops with constant conditions, returning the CFG nodes 
        representing the start of the branch that is never executed.
        """
        dead_branch_nodes = []
        
        def get_const_value(expr: ast.AST) -> Optional[bool]:
            if isinstance(expr, ast.Constant):
                return bool(expr.value)
            if isinstance(expr, ast.NameConstant):
                return expr.value
            return None

        for node_id, node in self.nodes.items():
            if not isinstance(node, CFGNode) or not node.block:
                continue
            
            for stmt in node.block.statements:
                if isinstance(stmt, ast.If):
                    const_val = get_const_value(stmt.test)
                    if const_val is not None:
                        edges = self.get_outgoing_edges(node_id)
                        for edge in edges:
                            if const_val is True and edge.label == "False":
                                target_node = self.get_node(edge.target)
                                if isinstance(target_node, CFGNode):
                                    dead_branch_nodes.append(target_node)
                            elif const_val is False and edge.label == "True":
                                target_node = self.get_node(edge.target)
                                if isinstance(target_node, CFGNode):
                                    dead_branch_nodes.append(target_node)
                elif isinstance(stmt, ast.While):
                    const_val = get_const_value(stmt.test)
                    if const_val is False:
                        edges = self.get_outgoing_edges(node_id)
                        for edge in edges:
                            if edge.label == "True":
                                target_node = self.get_node(edge.target)
                                if isinstance(target_node, CFGNode):
                                    dead_branch_nodes.append(target_node)
        
        return dead_branch_nodes

    def get_cyclomatic_complexity(self) -> int:
        """
        Computes Cyclomatic Complexity: M = E - V + 2P
        For a single CFG, P = 1.
        """
        num_edges = len(self.edges)
        num_nodes = len(self.nodes)
        if num_nodes == 0:
            return 1
        return num_edges - num_nodes + 2

    def find_excessive_branching(self, threshold: int = 10) -> bool:
        """Returns True if the cyclomatic complexity exceeds the threshold."""
        return self.get_cyclomatic_complexity() > threshold
