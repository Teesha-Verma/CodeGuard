import ast
from typing import List, Dict, Any

class ImportAnalyzer(ast.NodeVisitor):
    """Identifies module imports and flags dangerous libraries."""
    
    DANGEROUS_IMPORTS = {
        "subprocess",
        "pickle",
        "ctypes",
        "shutil",
        "os.system",
        "sys",
        "builtins",
        "socket"
    }

    def __init__(self):
        self.imports = []
        self.dangerous_calls = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            if alias.name in self.DANGEROUS_IMPORTS:
                self.dangerous_calls.append({
                    "line": node.lineno,
                    "module": alias.name,
                    "pattern": "dangerous_import",
                    "message": f"Import of dangerous module '{alias.name}' detected. Ensure inputs are fully sanitized."
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        self.imports.append(module)
        if module in self.DANGEROUS_IMPORTS:
            self.dangerous_calls.append({
                "line": node.lineno,
                "module": module,
                "pattern": "dangerous_import",
                "message": f"Import of dangerous module '{module}' detected. Ensure inputs are fully sanitized."
            })
        for alias in node.names:
            full_name = f"{module}.{alias.name}"
            if full_name in self.DANGEROUS_IMPORTS or alias.name in self.DANGEROUS_IMPORTS:
                self.dangerous_calls.append({
                    "line": node.lineno,
                    "module": full_name,
                    "pattern": "dangerous_import",
                    "message": f"Import of dangerous component '{alias.name}' from module '{module}' detected."
                })
        self.generic_visit(node)

    def analyze(self, code: str) -> Dict[str, Any]:
        self.imports = []
        self.dangerous_calls = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return {
                "imports": self.imports,
                "dangerous_imports": self.dangerous_calls
            }
        except (SyntaxError, IndentationError):
            return {
                "imports": [],
                "dangerous_imports": []
            }
