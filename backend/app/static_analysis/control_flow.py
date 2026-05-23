import ast
from typing import Dict, Any, List

class ControlFlowAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.findings = []
        
    def visit_Return(self, node):
        self.generic_visit(node)
        
    def visit_Try(self, node):
        for handler in node.handlers:
            if handler.type is None:
                self.findings.append({
                    "type": "bare_except",
                    "line": getattr(handler, "lineno", node.lineno),
                    "message": "Bare except catches SystemExit/KeyboardInterrupt"
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
