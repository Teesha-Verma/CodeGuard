"""
Data Flow Builder — constructs a DataFlowGraph from Python AST.

Walks a module / function body and creates nodes for every variable
definition-site, parameter, literal, return value, attribute write,
and collection element write.  Edges record the data movement
(assignment, aliasing, parameter passing, etc.).
"""

from __future__ import annotations

import ast
from typing import Optional, Dict, List

from app.analysis.dataflow.constants import DataFlowNodeKind, DataFlowEdgeKind
from app.analysis.dataflow.graph.dataflow_node import DataFlowNode
from app.analysis.dataflow.graph.dataflow_edge import DataFlowEdge
from app.analysis.dataflow.graph.dataflow_graph import DataFlowGraph


class DataFlowBuilder:
    """Builds a :class:`DataFlowGraph` from a Python AST module."""

    def __init__(self, module_name: str = "", file_path: Optional[str] = None):
        self.module_name = module_name
        self.file_path = file_path
        self.graph = DataFlowGraph(module_name=module_name)
        self._counter: int = 0
        self._scope_stack: List[str] = ["<module>"]
        # Use-def chain: (scope, variable_name) -> most recent def node id
        self._def_map: Dict[str, str] = {}

    # ── helpers ───────────────────────────────────────────────────

    def _next_id(self, prefix: str = "df") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    @property
    def _scope(self) -> str:
        return ".".join(self._scope_stack)

    def _make_node(
        self,
        df_kind: DataFlowNodeKind,
        name: str,
        line: Optional[int] = None,
    ) -> DataFlowNode:
        node_id = self._next_id(df_kind.value)
        node = DataFlowNode(
            node_id=node_id,
            df_kind=df_kind,
            name=name,
            line=line,
            scope=self._scope,
            file_path=self.file_path,
        )
        self.graph.add_node(node)
        return node

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        df_kind: DataFlowEdgeKind,
        line: Optional[int] = None,
    ) -> DataFlowEdge:
        edge = DataFlowEdge(
            source=source_id,
            target=target_id,
            df_kind=df_kind,
            line=line,
            scope=self._scope,
        )
        self.graph.add_edge(edge)
        return edge

    # ── public entry point ───────────────────────────────────────

    def build(self, source: str) -> DataFlowGraph:
        """Parse *source* code and return the populated DataFlowGraph."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self.graph
        self._visit_body(tree.body)
        return self.graph

    def build_from_tree(self, tree: ast.AST) -> DataFlowGraph:
        """Build from an already-parsed AST tree."""
        if isinstance(tree, ast.Module):
            self._visit_body(tree.body)
        elif isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(tree)
        return self.graph

    # ── statement dispatcher ─────────────────────────────────────

    def _visit_body(self, stmts: List[ast.stmt]) -> None:
        for stmt in stmts:
            self._visit_stmt(stmt)

    def _visit_stmt(self, stmt: ast.stmt) -> None:
        if isinstance(stmt, ast.Assign):
            self._visit_assign(stmt)
        elif isinstance(stmt, ast.AnnAssign):
            self._visit_ann_assign(stmt)
        elif isinstance(stmt, ast.AugAssign):
            self._visit_aug_assign(stmt)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(stmt)
        elif isinstance(stmt, ast.ClassDef):
            self._visit_class(stmt)
        elif isinstance(stmt, ast.Return):
            self._visit_return(stmt)
        elif isinstance(stmt, ast.For):
            self._visit_for(stmt)
        elif isinstance(stmt, ast.While):
            self._visit_while(stmt)
        elif isinstance(stmt, ast.If):
            self._visit_if(stmt)
        elif isinstance(stmt, ast.With):
            self._visit_with(stmt)
        elif isinstance(stmt, ast.Try):
            self._visit_try(stmt)
        elif isinstance(stmt, ast.Expr):
            # bare expression — may be a call
            self._visit_expr_value(stmt.value)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            self._visit_import(stmt)

    # ── assignments ──────────────────────────────────────────────

    def _visit_assign(self, stmt: ast.Assign) -> None:
        rhs_node = self._node_from_expr(stmt.value, stmt.lineno)
        for target in stmt.targets:
            self._assign_target(target, rhs_node, stmt.lineno)

    def _visit_ann_assign(self, stmt: ast.AnnAssign) -> None:
        if stmt.value is not None:
            rhs_node = self._node_from_expr(stmt.value, stmt.lineno)
            self._assign_target(stmt.target, rhs_node, stmt.lineno)

    def _visit_aug_assign(self, stmt: ast.AugAssign) -> None:
        rhs_node = self._node_from_expr(stmt.value, stmt.lineno)
        target_name = self._target_name(stmt.target)
        if target_name:
            tgt_node = self._make_node(
                DataFlowNodeKind.VARIABLE, target_name, stmt.lineno
            )
            self._add_edge(
                rhs_node.id, tgt_node.id,
                DataFlowEdgeKind.AUGMENTED_ASSIGN, stmt.lineno,
            )

    def _assign_target(
        self,
        target: ast.AST,
        rhs_node: DataFlowNode,
        line: int,
    ) -> None:
        # Simple name
        if isinstance(target, ast.Name):
            tgt_node = self._make_node(
                DataFlowNodeKind.VARIABLE, target.id, line
            )
            self._add_edge(
                rhs_node.id, tgt_node.id,
                DataFlowEdgeKind.ASSIGNMENT, line,
            )
            # Record this definition for use-def chain
            self._def_map[self._def_key(target.id)] = tgt_node.id

        # Tuple / List unpacking
        elif isinstance(target, (ast.Tuple, ast.List)):
            for idx, elt in enumerate(target.elts):
                unpack_node = self._make_node(
                    DataFlowNodeKind.COLLECTION_ELEMENT,
                    f"{self._expr_label(rhs_node)}[{idx}]",
                    line,
                )
                self._add_edge(
                    rhs_node.id, unpack_node.id,
                    DataFlowEdgeKind.TUPLE_UNPACK, line,
                )
                self._assign_target(elt, unpack_node, line)

        # Attribute write: obj.attr = ...
        elif isinstance(target, ast.Attribute):
            attr_name = self._unparse(target)
            tgt_node = self._make_node(
                DataFlowNodeKind.ATTRIBUTE, attr_name, line
            )
            self._add_edge(
                rhs_node.id, tgt_node.id,
                DataFlowEdgeKind.ATTRIBUTE_WRITE, line,
            )

        # Subscript write: obj[key] = ...
        elif isinstance(target, ast.Subscript):
            sub_name = self._unparse(target)
            tgt_node = self._make_node(
                DataFlowNodeKind.COLLECTION_ELEMENT, sub_name, line
            )
            self._add_edge(
                rhs_node.id, tgt_node.id,
                DataFlowEdgeKind.COLLECTION_WRITE, line,
            )

        # Starred: *x = ...
        elif isinstance(target, ast.Starred) and isinstance(target.value, ast.Name):
            tgt_node = self._make_node(
                DataFlowNodeKind.VARIABLE, target.value.id, line
            )
            self._add_edge(
                rhs_node.id, tgt_node.id,
                DataFlowEdgeKind.ASSIGNMENT, line,
            )

    # ── expression → node ────────────────────────────────────────

    def _node_from_expr(self, expr: ast.expr, line: int) -> DataFlowNode:
        """Create or reference a node for an arbitrary rhs expression."""
        if isinstance(expr, ast.Name):
            use_node = self._make_node(DataFlowNodeKind.VARIABLE, expr.id, line)
            # Use-def chain: link from the most recent definition
            def_key = self._def_key(expr.id)
            if def_key in self._def_map:
                self._add_edge(
                    self._def_map[def_key], use_node.id,
                    DataFlowEdgeKind.ALIAS, line,
                )
            return use_node

        if isinstance(expr, ast.Constant):
            return self._make_node(
                DataFlowNodeKind.LITERAL, repr(expr.value), line
            )

        if isinstance(expr, ast.Attribute):
            return self._make_node(
                DataFlowNodeKind.ATTRIBUTE, self._unparse(expr), line
            )

        if isinstance(expr, ast.Subscript):
            return self._make_node(
                DataFlowNodeKind.COLLECTION_ELEMENT,
                self._unparse(expr), line,
            )

        if isinstance(expr, ast.Call):
            return self._visit_call_expr(expr, line)

        if isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
            container_node = self._make_node(
                DataFlowNodeKind.LITERAL,
                self._unparse(expr), line,
            )
            for elt in expr.elts:
                elt_node = self._node_from_expr(elt, line)
                self._add_edge(
                    elt_node.id, container_node.id,
                    DataFlowEdgeKind.COLLECTION_WRITE, line,
                )
            return container_node

        if isinstance(expr, ast.Dict):
            dict_node = self._make_node(
                DataFlowNodeKind.LITERAL,
                self._unparse(expr), line,
            )
            for val in expr.values:
                if val is not None:
                    val_node = self._node_from_expr(val, line)
                    self._add_edge(
                        val_node.id, dict_node.id,
                        DataFlowEdgeKind.COLLECTION_WRITE, line,
                    )
            return dict_node

        # fallback
        return self._make_node(
            DataFlowNodeKind.LITERAL, self._unparse(expr), line
        )

    def _visit_call_expr(self, call: ast.Call, line: int) -> DataFlowNode:
        func_label = self._unparse(call.func)
        result_node = self._make_node(
            DataFlowNodeKind.CALL_RESULT, f"{func_label}()", line
        )
        # link arguments → function-arg nodes → result
        for idx, arg in enumerate(call.args):
            arg_node = self._node_from_expr(arg, line)
            farg_node = self._make_node(
                DataFlowNodeKind.FUNCTION_ARG,
                f"{func_label}:arg{idx}", line,
            )
            self._add_edge(
                arg_node.id, farg_node.id,
                DataFlowEdgeKind.PARAMETER_PASS, line,
            )
            self._add_edge(
                farg_node.id, result_node.id,
                DataFlowEdgeKind.FUNCTION_CALL, line,
            )
        for kw in call.keywords:
            kw_label = kw.arg or "**kwargs"
            kw_val_node = self._node_from_expr(kw.value, line)
            farg_node = self._make_node(
                DataFlowNodeKind.FUNCTION_ARG,
                f"{func_label}:{kw_label}", line,
            )
            self._add_edge(
                kw_val_node.id, farg_node.id,
                DataFlowEdgeKind.PARAMETER_PASS, line,
            )
            self._add_edge(
                farg_node.id, result_node.id,
                DataFlowEdgeKind.FUNCTION_CALL, line,
            )
        return result_node

    def _visit_expr_value(self, expr: ast.expr) -> None:
        """Handle a bare expression statement (e.g. a standalone call)."""
        if isinstance(expr, ast.Call):
            self._visit_call_expr(expr, getattr(expr, "lineno", 0))

    # ── functions ────────────────────────────────────────────────

    def _visit_function(self, func: ast.AST) -> None:
        name = getattr(func, "name", "<lambda>")
        self._scope_stack.append(name)

        # parameters → nodes
        args_node = getattr(func, "args", None)
        if args_node:
            for arg in args_node.args:
                param_node = self._make_node(
                    DataFlowNodeKind.PARAMETER, arg.arg,
                    getattr(arg, "lineno", getattr(func, "lineno", None)),
                )
                # Register param in def_map so uses inside the body link back
                self._def_map[self._def_key(arg.arg)] = param_node.id

        self._visit_body(func.body)
        self._scope_stack.pop()

    def _visit_return(self, stmt: ast.Return) -> None:
        if stmt.value is not None:
            val_node = self._node_from_expr(stmt.value, stmt.lineno)
            ret_node = self._make_node(
                DataFlowNodeKind.RETURN_VALUE, "<return>", stmt.lineno
            )
            self._add_edge(
                val_node.id, ret_node.id,
                DataFlowEdgeKind.RETURN_PROPAGATION, stmt.lineno,
            )

    # ── classes ──────────────────────────────────────────────────

    def _visit_class(self, cls: ast.ClassDef) -> None:
        self._scope_stack.append(cls.name)
        self._visit_body(cls.body)
        self._scope_stack.pop()

    # ── control flow bodies ──────────────────────────────────────

    def _visit_for(self, stmt: ast.For) -> None:
        iter_node = self._node_from_expr(stmt.iter, stmt.lineno)
        self._assign_target(stmt.target, iter_node, stmt.lineno)
        self._visit_body(stmt.body)
        if stmt.orelse:
            self._visit_body(stmt.orelse)

    def _visit_while(self, stmt: ast.While) -> None:
        self._visit_body(stmt.body)
        if stmt.orelse:
            self._visit_body(stmt.orelse)

    def _visit_if(self, stmt: ast.If) -> None:
        self._visit_body(stmt.body)
        if stmt.orelse:
            self._visit_body(stmt.orelse)

    def _visit_with(self, stmt: ast.With) -> None:
        for item in stmt.items:
            if item.optional_vars is not None:
                ctx_node = self._node_from_expr(
                    item.context_expr, stmt.lineno
                )
                self._assign_target(item.optional_vars, ctx_node, stmt.lineno)
        self._visit_body(stmt.body)

    def _visit_try(self, stmt: ast.Try) -> None:
        self._visit_body(stmt.body)
        for handler in stmt.handlers:
            self._visit_body(handler.body)
        if stmt.orelse:
            self._visit_body(stmt.orelse)
        if stmt.finalbody:
            self._visit_body(stmt.finalbody)

    # ── imports ──────────────────────────────────────────────────

    def _visit_import(self, stmt: ast.AST) -> None:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                local_name = alias.asname or alias.name
                self._make_node(
                    DataFlowNodeKind.IMPORT, local_name,
                    getattr(stmt, "lineno", None),
                )
        elif isinstance(stmt, ast.ImportFrom):
            module = stmt.module or ""
            for alias in stmt.names:
                local_name = alias.asname or alias.name
                self._make_node(
                    DataFlowNodeKind.IMPORT,
                    f"{module}.{alias.name}" if module else alias.name,
                    getattr(stmt, "lineno", None),
                )

    # ── tiny helpers ─────────────────────────────────────────────

    def _def_key(self, name: str) -> str:
        """Scope-qualified key for the use-def map."""
        return f"{self._scope}::{name}"

    @staticmethod
    def _target_name(target: ast.AST) -> Optional[str]:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return DataFlowBuilder._unparse(target)
        return None

    @staticmethod
    def _unparse(node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return repr(node)

    @staticmethod
    def _expr_label(node: DataFlowNode) -> str:
        return node.name
