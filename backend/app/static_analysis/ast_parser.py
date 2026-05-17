import ast
from typing import List, Dict, Any

class PythonASTParser:
    """Uses Python's built-in ast module to extract basic structural metadata."""
    
    def parse(self, code: str, changed_lines: List[int]) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        result = []
        changed_lines_set = set(changed_lines)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    node_lines = set(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
                    
                    # If this function/class overlaps with changed lines
                    if node_lines.intersection(changed_lines_set):
                        item = {
                            "type": type(node).__name__,
                            "name": node.name,
                            "start_line": node.lineno,
                            "end_line": getattr(node, "end_lineno", None),
                        }
                        
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            item["args"] = [arg.arg for arg in node.args.args]
                            item["has_docstring"] = ast.get_docstring(node) is not None
                            item["is_async"] = isinstance(node, ast.AsyncFunctionDef)
                        
                        result.append(item)

        return result
