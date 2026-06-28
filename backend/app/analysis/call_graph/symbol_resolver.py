import ast
from typing import Dict, List, Set, Optional

class SymbolResolver:
    """Resolves names and calls to fully qualified function or class method definitions."""
    
    def __init__(self):
        # Maps module path (dot-separated, e.g. 'app.core.utils') to a dict of definitions
        # definitions mapping: name -> {'type': 'function'|'class'|'method', 'node': AST, 'lineno': int, 'class_name': str|None}
        self.definitions: Dict[str, Dict[str, dict]] = {}
        # List of all module paths discovered in the repository
        self.modules: Set[str] = set()

    def register_module(self, module_name: str) -> None:
        self.modules.add(module_name)
        if module_name not in self.definitions:
            self.definitions[module_name] = {}

    def register_definition(
        self,
        module_name: str,
        name: str,
        def_type: str,
        lineno: int,
        node: ast.AST,
        class_name: Optional[str] = None
    ) -> None:
        self.register_module(module_name)
        self.definitions[module_name][name] = {
            "type": def_type,
            "lineno": lineno,
            "node": node,
            "class_name": class_name
        }

    def get_imports(self, tree: ast.AST) -> Dict[str, str]:
        """
        Parses imports in a module tree.
        Returns a mapping of alias/local name -> fully qualified name/module.
        """
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    imports[local_name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    if alias.name == "*":
                        imports["*"] = module
                    else:
                        imports[local_name] = f"{module}.{alias.name}" if module else alias.name
        return imports

    def resolve_call(
        self,
        call_node: ast.Call,
        current_module: str,
        current_class: Optional[str],
        module_imports: Dict[str, str],
        local_vars: Dict[str, str]
    ) -> List[str]:
        """
        Resolves the target of a Call node to fully qualified name(s).
        Returns a list of potential fully qualified callee names.
        """
        func = call_node.func
        
        # Case 1: Direct name call, e.g. `foo()`
        if isinstance(func, ast.Name):
            name = func.id
            
            # Check if name is defined locally in the current module
            if name in self.definitions.get(current_module, {}):
                defn = self.definitions[current_module][name]
                if defn["class_name"]:
                    return [f"{current_module}.{defn['class_name']}.{name}"]
                return [f"{current_module}.{name}"]
                
            # Check imports
            if name in module_imports:
                fqn = module_imports[name]
                return [fqn]
                
            # Check if there is a wildcard import and the name is defined in that module
            if "*" in module_imports:
                wildcard_module = module_imports["*"]
                if wildcard_module in self.definitions and name in self.definitions[wildcard_module]:
                    defn = self.definitions[wildcard_module][name]
                    if defn["class_name"]:
                        return [f"{wildcard_module}.{defn['class_name']}.{name}"]
                    return [f"{wildcard_module}.{name}"]
                    
            return [name]

        # Case 2: Attribute call, e.g. `self.foo()`, `obj.foo()`, `module.foo()`
        elif isinstance(func, ast.Attribute):
            attr_name = func.attr
            
            # Sub-case 2a: `self.foo()` or `cls.foo()` inside a class
            if isinstance(func.value, ast.Name) and func.value.id in ("self", "cls") and current_class:
                fqn = f"{current_module}.{current_class}.{attr_name}"
                return [fqn]
                
            # Sub-case 2b: `obj.foo()` where obj is a local variable with known class type
            if isinstance(func.value, ast.Name):
                obj_name = func.value.id
                if obj_name in local_vars:
                    class_type = local_vars[obj_name]
                    resolved_class = self._resolve_class_fqn(class_type, current_module, module_imports)
                    return [f"{resolved_class}.{attr_name}"]
                    
                # Sub-case 2c: `module.foo()` where `module` is imported
                if obj_name in module_imports:
                    imported_module = module_imports[obj_name]
                    return [f"{imported_module}.{attr_name}"]
                    
            # Sub-case 2d: nested attributes, e.g. `a.b.c.foo()`
            prefix = self._unparse_attribute(func.value)
            if prefix:
                parts = prefix.split(".")
                first_part = parts[0]
                if first_part in module_imports:
                    resolved_prefix = module_imports[first_part]
                    if len(parts) > 1:
                        resolved_prefix = f"{resolved_prefix}.{'.'.join(parts[1:])}"
                    return [f"{resolved_prefix}.{attr_name}"]
                    
            # Sub-case 2e: Best-effort global search for class methods matching `attr_name`
            matches = []
            for mod, defs in self.definitions.items():
                for name, defn in defs.items():
                    if defn["class_name"] and name == attr_name:
                        matches.append(f"{mod}.{defn['class_name']}.{attr_name}")
            if matches:
                return matches

            return [f"*.{attr_name}"]

        return []

    def _resolve_class_fqn(self, class_name: str, current_module: str, module_imports: Dict[str, str]) -> str:
        parts = class_name.split(".")
        first_part = parts[0]
        if first_part in module_imports:
            resolved = module_imports[first_part]
            if len(parts) > 1:
                return f"{resolved}.{'.'.join(parts[1:])}"
            return resolved
        if class_name in self.definitions.get(current_module, {}):
            return f"{current_module}.{class_name}"
        return class_name

    def _unparse_attribute(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._unparse_attribute(node.value)
            if val:
                return f"{val}.{node.attr}"
        return None
