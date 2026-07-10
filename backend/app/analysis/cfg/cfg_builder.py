import ast
from typing import List, Tuple, Optional
from app.analysis.graph.graph_types import NodeKind, EdgeKind
from app.analysis.cfg.basic_block import BasicBlock
from app.analysis.cfg.cfg_node import CFGNode
from app.analysis.cfg.cfg_edge import CFGEdge
from app.analysis.cfg.cfg_graph import CFGGraph

class CFGBuilder:
    """Constructs a Control Flow Graph (CFG) from a function's AST representation."""
    
    def __init__(self):
        self.graph: Optional[CFGGraph] = None
        self.block_counter: int = 0
        self.loop_stack: List[Tuple[CFGNode, CFGNode]] = []  # List of (header_node, exit_node)
        self.current_block: Optional[CFGNode] = None

    def _next_block_id(self) -> str:
        self.block_counter += 1
        return f"block_{self.block_counter}"

    def _new_node(self, kind: NodeKind, label: Optional[str] = None) -> CFGNode:
        block_id = self._next_block_id()
        block = BasicBlock(block_id)
        node = CFGNode(node_id=block_id, kind=kind, label=label, block=block)
        if self.graph:
            self.graph.add_node(node)
        return node

    def _add_to_current_block(self, stmt: ast.AST) -> None:
        if self.current_block is None:
            # Unreachable block
            self.current_block = self._new_node(NodeKind.CFG_STATEMENT, label="Unreachable")
        elif self.current_block.kind != NodeKind.CFG_STATEMENT:
            # If current block is control structure (branch/join), start a new statement block
            new_stmt_block = self._new_node(NodeKind.CFG_STATEMENT)
            self.graph.add_edge(CFGEdge(self.current_block.id, new_stmt_block.id))
            self.current_block = new_stmt_block
            
        self.current_block.block.add_statement(stmt)
        # Update node label dynamically to show statements
        self.current_block.label = self.current_block.block.get_label()

    def build(self, func_node: ast.AST) -> CFGGraph:
        """Builds and returns the CFGGraph for the given function AST node."""
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("CFGBuilder expects ast.FunctionDef or ast.AsyncFunctionDef")

        self.graph = CFGGraph(function_name=func_node.name)
        self.block_counter = 0
        self.loop_stack = []
        
        # Define Entry and Exit Nodes
        entry_node = CFGNode(node_id="ENTRY", kind=NodeKind.CFG_ENTRY, label="ENTRY")
        exit_node = CFGNode(node_id="EXIT", kind=NodeKind.CFG_EXIT, label="EXIT")
        
        self.graph.add_node(entry_node)
        self.graph.add_node(exit_node)
        self.graph.entry_node = entry_node
        self.graph.exit_node = exit_node
        
        # Start initial statement block
        self.current_block = self._new_node(NodeKind.CFG_STATEMENT)
        self.graph.add_edge(CFGEdge(entry_node.id, self.current_block.id))
        
        self._process_statements(func_node.body)
        
        # Connect final block to Exit (if reachable)
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, exit_node.id))
            
        return self.graph

    def _process_statements(self, statements: List[ast.AST]) -> None:
        for stmt in statements:
            if isinstance(stmt, ast.If):
                self._process_if(stmt)
            elif isinstance(stmt, ast.While):
                self._process_while(stmt)
            elif isinstance(stmt, ast.For):
                self._process_for(stmt)
            elif isinstance(stmt, ast.Return):
                self._process_return(stmt)
            elif isinstance(stmt, ast.Raise):
                self._process_raise(stmt)
            elif isinstance(stmt, ast.Break):
                self._process_break(stmt)
            elif isinstance(stmt, ast.Continue):
                self._process_continue(stmt)
            elif isinstance(stmt, ast.Try):
                self._process_try(stmt)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._add_to_current_block(stmt)
            else:
                self._add_to_current_block(stmt)

    def _process_if(self, stmt: ast.If) -> None:
        test_expr_str = ast.unparse(stmt.test) if hasattr(ast, "unparse") else "if condition"
        if_node = self._new_node(NodeKind.CFG_BRANCH, label=f"if {test_expr_str}")
        if_node.block.add_statement(stmt)
        
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, if_node.id))
            
        # Process True/Then branch
        true_start = self._new_node(NodeKind.CFG_STATEMENT)
        self.graph.add_edge(CFGEdge(if_node.id, true_start.id, kind=EdgeKind.CFG_TRUE, label="True"))
        self.current_block = true_start
        self._process_statements(stmt.body)
        true_end = self.current_block
        
        # Process False/Else branch
        false_start = self._new_node(NodeKind.CFG_STATEMENT)
        self.graph.add_edge(CFGEdge(if_node.id, false_start.id, kind=EdgeKind.CFG_FALSE, label="False"))
        self.current_block = false_start
        self._process_statements(stmt.orelse)
        false_end = self.current_block
        
        # Join node
        if true_end is None and false_end is None:
            self.current_block = None
        else:
            join_node = self._new_node(NodeKind.CFG_JOIN, label="IfJoin")
            if true_end is not None:
                self.graph.add_edge(CFGEdge(true_end.id, join_node.id))
            if false_end is not None:
                self.graph.add_edge(CFGEdge(false_end.id, join_node.id))
            self.current_block = join_node

    def _process_while(self, stmt: ast.While) -> None:
        test_expr_str = ast.unparse(stmt.test) if hasattr(ast, "unparse") else "while condition"
        header_node = self._new_node(NodeKind.CFG_BRANCH, label=f"while {test_expr_str}")
        header_node.block.add_statement(stmt)
        
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, header_node.id))
            
        exit_node = self._new_node(NodeKind.CFG_JOIN, label="WhileExit")
        self.graph.add_edge(CFGEdge(header_node.id, exit_node.id, kind=EdgeKind.CFG_FALSE, label="False"))
        
        self.loop_stack.append((header_node, exit_node))
        
        body_start = self._new_node(NodeKind.CFG_STATEMENT)
        self.graph.add_edge(CFGEdge(header_node.id, body_start.id, kind=EdgeKind.CFG_TRUE, label="True"))
        
        self.current_block = body_start
        self._process_statements(stmt.body)
        
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, header_node.id))
            
        self.loop_stack.pop()
        
        if stmt.orelse:
            self.current_block = exit_node
            self._process_statements(stmt.orelse)
        else:
            self.current_block = exit_node

    def _process_for(self, stmt: ast.For) -> None:
        target_str = ast.unparse(stmt.target) if hasattr(ast, "unparse") else "target"
        iter_str = ast.unparse(stmt.iter) if hasattr(ast, "unparse") else "iterable"
        header_node = self._new_node(NodeKind.CFG_BRANCH, label=f"for {target_str} in {iter_str}")
        header_node.block.add_statement(stmt)
        
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, header_node.id))
            
        exit_node = self._new_node(NodeKind.CFG_JOIN, label="ForExit")
        self.graph.add_edge(CFGEdge(header_node.id, exit_node.id, kind=EdgeKind.CFG_FALSE, label="False"))
        
        self.loop_stack.append((header_node, exit_node))
        
        body_start = self._new_node(NodeKind.CFG_STATEMENT)
        self.graph.add_edge(CFGEdge(header_node.id, body_start.id, kind=EdgeKind.CFG_TRUE, label="True"))
        
        self.current_block = body_start
        self._process_statements(stmt.body)
        
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, header_node.id))
            
        self.loop_stack.pop()
        
        if stmt.orelse:
            self.current_block = exit_node
            self._process_statements(stmt.orelse)
        else:
            self.current_block = exit_node

    def _process_return(self, stmt: ast.Return) -> None:
        self._add_to_current_block(stmt)
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, self.graph.exit_node.id))
        self.current_block = None

    def _process_raise(self, stmt: ast.Raise) -> None:
        self._add_to_current_block(stmt)
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, self.graph.exit_node.id, label="Exception"))
        self.current_block = None

    def _process_break(self, stmt: ast.Break) -> None:
        self._add_to_current_block(stmt)
        if self.loop_stack and self.current_block is not None:
            _, loop_exit = self.loop_stack[-1]
            self.graph.add_edge(CFGEdge(self.current_block.id, loop_exit.id))
        self.current_block = None

    def _process_continue(self, stmt: ast.Continue) -> None:
        self._add_to_current_block(stmt)
        if self.loop_stack and self.current_block is not None:
            loop_header, _ = self.loop_stack[-1]
            self.graph.add_edge(CFGEdge(self.current_block.id, loop_header.id))
        self.current_block = None

    def _process_try(self, stmt: ast.Try) -> None:
        try_header = self._new_node(NodeKind.CFG_STATEMENT, label=f"Try [{getattr(stmt, 'lineno', '?')}]")
        if self.current_block is not None:
            self.graph.add_edge(CFGEdge(self.current_block.id, try_header.id))
            
        self.current_block = try_header
        self._process_statements(stmt.body)
        try_end = self.current_block
        
        handler_ends = []
        for handler in stmt.handlers:
            handler_start = self._new_node(NodeKind.CFG_STATEMENT, label=f"Except [{getattr(handler, 'lineno', '?')}]")
            self.graph.add_edge(CFGEdge(try_header.id, handler_start.id, label="Exception"))
            self.current_block = handler_start
            self._process_statements(handler.body)
            if self.current_block is not None:
                handler_ends.append(self.current_block)
                
        if stmt.orelse:
            if try_end is not None:
                self.current_block = try_end
                self._process_statements(stmt.orelse)
                try_end = self.current_block
                
        join_node = self._new_node(NodeKind.CFG_JOIN, label="TryJoin")
        has_incoming = False
        if try_end is not None:
            self.graph.add_edge(CFGEdge(try_end.id, join_node.id))
            has_incoming = True
        for h_end in handler_ends:
            self.graph.add_edge(CFGEdge(h_end.id, join_node.id))
            has_incoming = True
            
        if has_incoming:
            self.current_block = join_node
        else:
            self.current_block = None
            
        if stmt.finalbody:
            final_block = self._new_node(NodeKind.CFG_STATEMENT, label="Finally")
            if self.current_block is not None:
                self.graph.add_edge(CFGEdge(self.current_block.id, final_block.id))
            self.current_block = final_block
            self._process_statements(stmt.finalbody)
