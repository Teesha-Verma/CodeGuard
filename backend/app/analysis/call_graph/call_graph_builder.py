import ast
from typing import Dict, List, Optional
from app.analysis.graph.graph_types import NodeKind
from app.analysis.call_graph.call_graph import CallGraph, CallGraphNode, CallGraphEdge
from app.analysis.call_graph.symbol_resolver import SymbolResolver

class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, module_name: str, resolver: SymbolResolver, graph: CallGraph, file_path: Optional[str] = None):
        self.module_name: str = module_name
        self.resolver: SymbolResolver = resolver
        self.graph: CallGraph = graph
        self.file_path: Optional[str] = file_path
        
        self.current_class: Optional[str] = None
        self.current_caller: Optional[str] = None
        self.local_vars: Dict[str, str] = {}  # var_name -> class_type
        self.imports: Dict[str, str] = {}

    def visit_Module(self, node: ast.Module):
        self.imports = self.resolver.get_imports(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function_or_method(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function_or_method(node)

    def _visit_function_or_method(self, node: ast.AST):
        name = getattr(node, "name")
        if self.current_class:
            caller_fqn = f"{self.module_name}.{self.current_class}.{name}"
            kind = NodeKind.CALL_METHOD
        else:
            caller_fqn = f"{self.module_name}.{name}"
            kind = NodeKind.CALL_FUNCTION

        old_caller = self.current_caller
        self.current_caller = caller_fqn
        
        old_local_vars = self.local_vars.copy()
        self.local_vars = {}

        caller_node = CallGraphNode(
            node_id=caller_fqn,
            kind=kind,
            label=caller_fqn,
            file_path=self.file_path,
            line_number=node.lineno
        )
        self.graph.add_node(caller_node)

        self.generic_visit(node)

        self.local_vars = old_local_vars
        self.current_caller = old_caller

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            class_name = node.value.func.id
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.local_vars[target.id] = class_name
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if self.current_caller:
            callees = self.resolver.resolve_call(
                node,
                current_module=self.module_name,
                current_class=self.current_class,
                module_imports=self.imports,
                local_vars=self.local_vars
            )
            
            for callee_fqn in callees:
                callee_defn = None
                parts = callee_fqn.split(".")
                
                if len(parts) >= 2:
                    for i in range(1, len(parts)):
                        possible_mod = ".".join(parts[:i])
                        possible_name = ".".join(parts[i:])
                        if possible_mod in self.resolver.definitions:
                            defs = self.resolver.definitions[possible_mod]
                            subparts = possible_name.split(".")
                            if len(subparts) == 2:
                                class_name, method_name = subparts
                                for name, d in defs.items():
                                    if d["class_name"] == class_name and name == method_name:
                                        callee_defn = d
                                        break
                            elif len(subparts) == 1:
                                name = subparts[0]
                                if name in defs:
                                    callee_defn = defs[name]
                                    break
                
                if callee_defn:
                    callee_kind = NodeKind.CALL_METHOD if callee_defn["class_name"] else NodeKind.CALL_FUNCTION
                    callee_node = CallGraphNode(
                        node_id=callee_fqn,
                        kind=callee_kind,
                        label=callee_fqn,
                        line_number=callee_defn["lineno"]
                    )
                else:
                    callee_kind = NodeKind.CALL_METHOD if "." in callee_fqn else NodeKind.CALL_FUNCTION
                    callee_node = CallGraphNode(
                        node_id=callee_fqn,
                        kind=callee_kind,
                        label=callee_fqn
                    )
                
                self.graph.add_node(callee_node)
                
                edge = CallGraphEdge(
                    source=self.current_caller,
                    target=callee_fqn,
                    call_site_line=node.lineno
                )
                self.graph.add_edge(edge)
                
        self.generic_visit(node)


class CallGraphBuilder:
    """Builds a repository-wide Call Graph by resolving imports and calls."""
    
    def __init__(self):
        self.resolver = SymbolResolver()
        self.graph = CallGraph()

    def build(self, sources: Dict[str, str], file_paths: Optional[Dict[str, str]] = None) -> CallGraph:
        """
        Builds the call graph from a dictionary mapping module name to its source code content.
        
        :param sources: Dict[str, str] mapping module name (e.g. 'app.core') to Python source code.
        :param file_paths: Optional Dict[str, str] mapping module name to source file path.
        """
        file_paths = file_paths or {}
        parsed_trees: Dict[str, ast.AST] = {}
        
        for module_name, code in sources.items():
            try:
                tree = ast.parse(code)
                parsed_trees[module_name] = tree
                self.resolver.register_module(module_name)
                
                self._discover_definitions(tree, module_name)
            except (SyntaxError, IndentationError):
                continue

        for module_name, tree in parsed_trees.items():
            file_path = file_paths.get(module_name)
            visitor = CallGraphVisitor(module_name, self.resolver, self.graph, file_path)
            visitor.visit(tree)
            
        return self.graph

    def _discover_definitions(self, tree: ast.AST, module_name: str) -> None:
        """Scan top-level of module to find function/class/method definitions."""
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.resolver.register_definition(
                    module_name=module_name,
                    name=node.name,
                    def_type="function",
                    lineno=node.lineno,
                    node=node
                )
            elif isinstance(node, ast.ClassDef):
                self.resolver.register_definition(
                    module_name=module_name,
                    name=node.name,
                    def_type="class",
                    lineno=node.lineno,
                    node=node
                )
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.resolver.register_definition(
                            module_name=module_name,
                            name=subnode.name,
                            def_type="method",
                            lineno=subnode.lineno,
                            node=subnode,
                            class_name=node.name
                        )
