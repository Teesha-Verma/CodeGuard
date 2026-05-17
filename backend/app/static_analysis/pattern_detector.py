import ast
from typing import Dict, List, Any

class PatternDetector(ast.NodeVisitor):
    """Detects dangerous patterns like mutable defaults and bad iterators."""
    
    def __init__(self):
        self.findings = []
        
    def visit_FunctionDef(self, node):
        # Check for mutable defaults
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append({
                    "type": "mutable_default",
                    "line": getattr(node, "lineno", 1),
                    "message": f"Mutable default argument in function '{node.name}'"
                })
        self.generic_visit(node)
        
    def visit_For(self, node):
        # Look for list mutation inside loop
        if isinstance(node.iter, ast.Name):
            iterable_name = node.iter.id
            for body_node in ast.walk(node):
                if isinstance(body_node, ast.Call):
                    if isinstance(body_node.func, ast.Attribute):
                        if isinstance(body_node.func.value, ast.Name) and body_node.func.value.id == iterable_name:
                            if body_node.func.attr in ("remove", "append", "extend", "pop", "clear"):
                                self.findings.append({
                                    "type": "mutation_during_iteration",
                                    "line": getattr(body_node, "lineno", node.lineno),
                                    "message": f"Mutation of iterable '{iterable_name}' during iteration"
                                })
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                self.findings.append({
                    "type": "dangerous_builtin",
                    "line": getattr(node, "lineno", 1),
                    "message": f"Use of dangerous built-in '{node.func.id}'"
                })
        self.generic_visit(node)

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        self.findings = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.findings
        except SyntaxError:
            return []
