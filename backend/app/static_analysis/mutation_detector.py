import ast
from typing import List, Dict, Any

class MutationDetector(ast.NodeVisitor):
    """Detects dangerous state mutation patterns using targeted AST traversal."""
    
    def __init__(self):
        self.findings = []
        self.current_class = None

    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node
        
        # Check for obvious shared mutable state default assignments at class scope
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(item.value, (ast.List, ast.Dict, ast.Set)):
                            self.findings.append({
                                "line": item.lineno,
                                "pattern": "shared_mutable_class_state",
                                "message": f"Class variable '{target.id}' in '{node.name}' has a mutable default ({type(item.value).__name__}). This creates shared state across all instances."
                            })
                            
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_For(self, node):
        # Look for list mutation inside loop
        if isinstance(node.iter, ast.Name):
            iterable_name = node.iter.id
            self._check_body_mutations(node.body, iterable_name)
        elif isinstance(node.iter, ast.Attribute) and isinstance(node.iter.value, ast.Name):
            # Handles things like 'self.items'
            iterable_name = f"{node.iter.value.id}.{node.iter.attr}"
            self._check_body_mutations(node.body, iterable_name)
            
        self.generic_visit(node)

    def visit_While(self, node):
        # We can also check while loop conditions if they depend on collection size and mutate
        self.generic_visit(node)

    def _check_body_mutations(self, body: List[ast.stmt], iterable_name: str):
        for body_node in ast.walk(ast.Module(body=body, type_ignores=[])):
            if isinstance(body_node, ast.Call) and isinstance(body_node.func, ast.Attribute):
                # e.g., items.remove(x) or self.items.remove(x)
                caller_name = self._resolve_attribute_name(body_node.func.value)
                if caller_name == iterable_name:
                    if body_node.func.attr in ("remove", "append", "extend", "pop", "clear", "insert"):
                        self.findings.append({
                            "line": body_node.lineno,
                            "pattern": "list mutation during iteration",
                            "message": f"Modifying list '{iterable_name}' during traversal can cause skipped elements or runtime instability."
                        })

    def _resolve_attribute_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._resolve_attribute_name(node.value)
            if val:
                return f"{val}.{node.attr}"
        return ""

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        self.findings = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.findings
        except (SyntaxError, IndentationError):
            return []
