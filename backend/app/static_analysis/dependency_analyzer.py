import ast
from typing import Dict, List, Any

class DependencyAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "line": getattr(node, "lineno", 1),
                "type": "import"
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append({
                "module": getattr(node, "module", ""),
                "name": alias.name,
                "line": getattr(node, "lineno", 1),
                "type": "import_from"
            })
        self.generic_visit(node)
        
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        self.imports = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.imports
        except SyntaxError:
            return []
