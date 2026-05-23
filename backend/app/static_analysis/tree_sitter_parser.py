import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from typing import List, Dict, Any, Optional

class TreeSitterParser:
    """Uses tree-sitter for robust, language-agnostic structural parsing."""
    
    def __init__(self, language: str = "python"):
        self.language = language
        if language == "python":
            self.ts_lang = Language(tspython.language())
        else:
            raise NotImplementedError(f"Language {language} not supported yet in Tree-sitter")
            
        self.parser = Parser(self.ts_lang)

    def get_functions(self, code_bytes: bytes) -> List[Dict[str, Any]]:
        tree = self.parser.parse(code_bytes)
        root = tree.root_node
        
        # Simple query for function definitions
        query_str = """
        (function_definition
          name: (identifier) @func.name) @func.def
        """
        query = self.ts_lang.query(query_str)
        captures = query.captures(root)
        
        functions = []
        
        # Format can vary depending on tree-sitter bindings version.
        if isinstance(captures, dict):
            # Dict mapping Node to capture name
            for node, capture_name in captures.items():
                if capture_name == "func.def":
                    functions.append({
                        "type": "function",
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "name": self._get_child_name(node, "name", code_bytes)
                    })
        elif isinstance(captures, list):
            # List of (Node, capture_name) tuples
            for node, capture_name in captures:
                if capture_name == "func.def":
                    functions.append({
                        "type": "function",
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "name": self._get_child_name(node, "name", code_bytes)
                    })
                    
        return functions

    def _get_child_name(self, node, field_name: str, code_bytes: bytes) -> Optional[str]:
        child = node.child_by_field_name(field_name)
        if child:
            return code_bytes[child.start_byte:child.end_byte].decode("utf8", errors="ignore")
        return None
