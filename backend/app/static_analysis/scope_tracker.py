import ast
from typing import List, Dict, Any

class ScopeTracker(ast.NodeVisitor):
    """Tracks variable scope to flag global modifications and shadowing issues."""
    
    def __init__(self):
        self.findings = []
        self.global_variables = set()
        self.current_function = None

    def visit_Module(self, node):
        # 1. First pass: collect all top-level module globals
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.global_variables.add(target.id)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.global_variables.add(item.name)
        
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node)

    def _visit_func(self, node):
        prev_func = self.current_function
        self.current_function = node
        
        # Look for 'global' keyword declarations and shadowing within this function
        for child in ast.walk(node):
            if isinstance(child, ast.Global):
                for name in child.names:
                    self.findings.append({
                        "line": child.lineno,
                        "pattern": "global_modification",
                        "message": f"Modification of global variable '{name}' inside function '{node.name}' violates pure-function boundaries."
                    })
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        # Detect shadowing of global variables
                        if target.id in self.global_variables:
                            # Verify if it was declared global in this function
                            has_global_decl = any(
                                isinstance(g, ast.Global) and target.id in g.names
                                for g in ast.walk(node)
                            )
                            if not has_global_decl:
                                self.findings.append({
                                    "line": child.lineno,
                                    "pattern": "variable_shadowing",
                                    "message": f"Local variable '{target.id}' shadows a global variable of the same name defined at module scope."
                                })

        self.generic_visit(node)
        self.current_function = prev_func

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        self.findings = []
        self.global_variables = set()
        self.current_function = None
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.findings
        except (SyntaxError, IndentationError):
            return []
