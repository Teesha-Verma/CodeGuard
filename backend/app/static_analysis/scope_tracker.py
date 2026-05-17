import ast
from typing import Dict, List, Any

class ScopeTracker(ast.NodeVisitor):
    """Walks the AST to identify variable scopes, globals, and shadows."""
    
    def __init__(self):
        self.scopes = []
        self.current_scope = "global"
        self.variables = {"global": set()}

    def visit_FunctionDef(self, node):
        prev_scope = self.current_scope
        self.current_scope = node.name
        self.variables[node.name] = set()
        
        # Add arguments to scope
        for arg in node.args.args:
            self.variables[node.name].add(arg.arg)
            
        self.generic_visit(node)
        
        self.scopes.append({
            "scope": node.name,
            "variables": list(self.variables[node.name]),
            "start_line": node.lineno
        })
        self.current_scope = prev_scope

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                if self.current_scope in self.variables:
                    self.variables[self.current_scope].add(target.id)
        self.generic_visit(node)
        
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        self.scopes = []
        self.variables = {"global": set()}
        self.current_scope = "global"
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.scopes
        except SyntaxError:
            return []
