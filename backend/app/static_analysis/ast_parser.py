import ast
import logging
from typing import List, Dict, Any

class PythonASTParser:
    """Uses Python's built-in ast module to extract deep, grounded structural intelligence."""
    
    def __init__(self):
        self.logger = logging.getLogger("codeguard.ast_parser")

    def _run_ast_rule(self, rule_name: str, rule_func, *args, **kwargs):
        """Conceptual per-rule runner logic providing fault isolation."""
        try:
            return rule_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"AST rule {rule_name} encountered an error: {e}. Isolation active.")
            return []

    def parse(self, code: str, changed_lines: List[int]) -> Dict[str, Any]:
        """
        Parses python source code and extracts high-fidelity structural features.
        Returns a dictionary with functions, classes, control structures, async alerts,
        and isolated AST rules findings.
        """
        try:
            tree = ast.parse(code)
        except (SyntaxError, IndentationError):
            return {
                "functions": [],
                "classes": [],
                "control_structures": [],
                "async_issues": [],
                "ast_rules_findings": []
            }

        functions = []
        classes = []
        control_structures = []
        async_issues = []
        
        # Track async function names to detect un-awaited async calls
        async_func_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_func_names.add(node.name)

        changed_lines_set = set(changed_lines)

        class ASTFeatureVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_function = None
                self.loop_depth = 0

            def visit_FunctionDef(self, node):
                self._visit_func(node, is_async=False)

            def visit_AsyncFunctionDef(self, node):
                self._visit_func(node, is_async=True)

            def _visit_func(self, node, is_async: bool):
                prev_func = self.current_function
                self.current_function = node.name
                
                # Check recursion
                is_recursive = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id == node.name:
                            is_recursive = True
                            break

                # Extract arguments
                args = [arg.arg for arg in node.args.args]
                
                # Check async def with missing await
                if is_async:
                    has_await = any(isinstance(child, ast.Await) for child in ast.walk(node))
                    if not has_await:
                        async_issues.append({
                            "line": node.lineno,
                            "type": "async_missing_await",
                            "message": f"Async function '{node.name}' does not contain any 'await' statements."
                        })

                # Check if this function has any changed lines
                node_lines = set(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
                is_changed = bool(node_lines.intersection(changed_lines_set)) if changed_lines_set else True

                functions.append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "args": args,
                    "is_async": is_async,
                    "is_recursive": is_recursive,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "is_changed": is_changed
                })

                self.generic_visit(node)
                self.current_function = prev_func

            def visit_ClassDef(self, node):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                        bases.append(f"{base.value.id}.{base.attr}")

                methods = []
                for body_item in node.body:
                    if isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(body_item.name)

                node_lines = set(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
                is_changed = bool(node_lines.intersection(changed_lines_set)) if changed_lines_set else True

                classes.append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "bases": bases,
                    "methods": methods,
                    "is_changed": is_changed
                })
                self.generic_visit(node)

            def visit_For(self, node):
                self._visit_loop(node)

            def visit_While(self, node):
                self._visit_loop(node)

            def _visit_loop(self, node):
                self.loop_depth += 1
                
                # Check for nesting
                is_nested = self.loop_depth > 1
                control_structures.append({
                    "type": type(node).__name__,
                    "line": node.lineno,
                    "nesting_depth": self.loop_depth,
                    "is_nested": is_nested
                })
                
                self.generic_visit(node)
                self.loop_depth -= 1

        visitor = ASTFeatureVisitor()
        visitor.visit(tree)

        # Detect missing awaits by checking calls to async functions that are not wrapped in ast.Await
        class AwaitCheckVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_await = False

            def visit_Await(self, node):
                prev = self.in_await
                self.in_await = True
                self.generic_visit(node)
                self.in_await = prev

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in async_func_names:
                    if not self.in_await:
                        async_issues.append({
                            "line": node.lineno,
                            "type": "missing_await_call",
                            "message": f"Async function '{node.func.id}' is called but not awaited."
                        })
                self.generic_visit(node)

        AwaitCheckVisitor().visit(tree)

        # ── PHASE 2: STRICT EXECUTION ORDER OF AST RULE CHECKS ──────────────────
        ast_rules_findings = []

        # FIRST LEVEL: High Precision, Low False-Positive Risk
        ast_rules_findings.extend(self._run_ast_rule("eval_detection", self._check_eval, tree))
        ast_rules_findings.extend(self._run_ast_rule("exec_detection", self._check_exec, tree))
        ast_rules_findings.extend(self._run_ast_rule("unsafe_subprocess", self._check_unsafe_subprocess, tree))
        ast_rules_findings.extend(self._run_ast_rule("unsafe_pickle", self._check_unsafe_pickle, tree))
        ast_rules_findings.extend(self._run_ast_rule("nested_loop", self._check_nested_loops, tree))
        ast_rules_findings.extend(self._run_ast_rule("variable_shadowing", self._check_variable_shadowing, tree))

        # SECOND LEVEL: Moderate Complexity
        ast_rules_findings.extend(self._run_ast_rule("mutation_during_iteration", self._check_mutation_during_iteration, tree))
        ast_rules_findings.extend(self._run_ast_rule("unsafe_global_mutation", self._check_unsafe_global_mutation, tree))

        # LAST LEVEL: Heuristics, Higher False-Positive Risk
        ast_rules_findings.extend(self._run_ast_rule("recursion_risk", self._check_recursion_risk, tree))
        ast_rules_findings.extend(self._run_ast_rule("async_misuse", self._check_async_misuse, tree))

        return {
            "functions": functions,
            "classes": classes,
            "control_structures": control_structures,
            "async_issues": async_issues,
            "ast_rules_findings": ast_rules_findings
        }

    # ── AST RULE IMPLEMENTATIONS ──────────────────────────────────────────

    def _check_eval(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
                findings.append({
                    "rule_name": "eval_detection",
                    "line": node.lineno,
                    "message": f"AST Node: Use of dangerous built-in 'eval' detected on line {node.lineno}"
                })
        return findings

    def _check_exec(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "exec":
                findings.append({
                    "rule_name": "exec_detection",
                    "line": node.lineno,
                    "message": f"AST Node: Use of dangerous built-in 'exec' detected on line {node.lineno}"
                })
        return findings

    def _check_unsafe_subprocess(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                is_subprocess = False
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                    is_subprocess = node.func.attr in ("run", "Popen", "call", "check_call", "check_output")
                elif isinstance(node.func, ast.Name) and node.func.id in ("run", "Popen", "call", "check_call", "check_output"):
                    is_subprocess = True
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "system":
                    findings.append({
                        "rule_name": "unsafe_subprocess",
                        "line": node.lineno,
                        "message": f"AST Node: Unsafe os.system call detected on line {node.lineno}"
                    })
                    continue
                
                if is_subprocess:
                    shell_true = False
                    for kw in node.keywords:
                        if kw.arg == "shell":
                            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                shell_true = True
                            elif isinstance(kw.value, ast.NameConstant) and kw.value.value is True:
                                shell_true = True
                    
                    first_arg_dynamic = False
                    if node.args:
                        arg0 = node.args[0]
                        if isinstance(arg0, ast.List):
                            for elt in arg0.elts:
                                if not isinstance(elt, ast.Constant) and not (isinstance(elt, ast.NameConstant) if hasattr(ast, "NameConstant") else False):
                                    first_arg_dynamic = True
                        elif not isinstance(arg0, ast.Constant) and not (isinstance(arg0, ast.NameConstant) if hasattr(ast, "NameConstant") else False):
                            first_arg_dynamic = True

                    if shell_true:
                        findings.append({
                            "rule_name": "unsafe_subprocess",
                            "line": node.lineno,
                            "message": f"AST Node: Unsafe subprocess call with shell=True on line {node.lineno}"
                        })
                    elif first_arg_dynamic:
                        findings.append({
                            "rule_name": "unsafe_subprocess",
                            "line": node.lineno,
                            "message": f"AST Node: Subprocess call with dynamic command on line {node.lineno}"
                        })
        return findings

    def _check_unsafe_pickle(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                is_pickle = False
                func_name = ""
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in ("pickle", "cPickle"):
                    is_pickle = node.func.attr in ("load", "loads")
                    func_name = f"pickle.{node.func.attr}"
                elif isinstance(node.func, ast.Name) and node.func.id in ("load", "loads"):
                    is_pickle = True
                    func_name = node.func.id
                
                if is_pickle:
                    findings.append({
                        "rule_name": "unsafe_pickle",
                        "line": node.lineno,
                        "message": f"AST Node: Unsafe deserialization call '{func_name}' detected on line {node.lineno}"
                    })
        return findings

    def _check_nested_loops(self, tree) -> List[Dict[str, Any]]:
        findings = []
        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
            
            def visit_For(self, node):
                self.current_depth += 1
                if self.current_depth > 2:
                    findings.append({
                        "rule_name": "nested_loop",
                        "line": node.lineno,
                        "message": f"AST Node: Nested loop deeper than 2 layers (depth={self.current_depth}) detected on line {node.lineno}"
                    })
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_While(self, node):
                self.current_depth += 1
                if self.current_depth > 2:
                    findings.append({
                        "rule_name": "nested_loop",
                        "line": node.lineno,
                        "message": f"AST Node: Nested loop deeper than 2 layers (depth={self.current_depth}) detected on line {node.lineno}"
                    })
                self.generic_visit(node)
                self.current_depth -= 1
                
        LoopVisitor().visit(tree)
        return findings

    def _check_variable_shadowing(self, tree) -> List[Dict[str, Any]]:
        findings = []
        BUILTINS = {
            "id", "list", "dict", "str", "int", "float", "len", "sum", "max", "min",
            "any", "all", "type", "dir", "set", "tuple", "bool", "range", "zip",
            "map", "filter", "open", "print", "abs", "round", "pow", "chr", "ord"
        }
        global_variables = set()
        
        for item in (tree.body if hasattr(tree, 'body') else []):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        global_variables.add(target.id)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                global_variables.add(item.name)

        class ShadowingVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                self._check_shadowing_in_func(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self._check_shadowing_in_func(node)
                self.generic_visit(node)

            def _check_shadowing_in_func(self, node):
                for arg in node.args.args:
                    if arg.arg in BUILTINS or arg.arg in global_variables:
                        findings.append({
                            "rule_name": "variable_shadowing",
                            "line": arg.lineno if hasattr(arg, "lineno") else node.lineno,
                            "message": f"AST Node: Local parameter '{arg.arg}' shadows a built-in or global variable on line {node.lineno}"
                        })
                
                for child in ast.walk(node):
                    assigned_names = []
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                assigned_names.append((target.id, child.lineno))
                    elif isinstance(child, ast.AnnAssign):
                        if isinstance(child.target, ast.Name):
                            assigned_names.append((child.target.id, child.lineno))
                    elif isinstance(child, ast.For):
                        if isinstance(child.target, ast.Name):
                            assigned_names.append((child.target.id, child.lineno))
                        elif isinstance(child.target, ast.Tuple):
                            for elt in child.target.elts:
                                if isinstance(elt, ast.Name):
                                    assigned_names.append((elt.id, child.lineno))

                    for name, line in assigned_names:
                        if name in BUILTINS or name in global_variables:
                            has_global_decl = any(
                                isinstance(g, ast.Global) and name in g.names
                                for g in ast.walk(node)
                            )
                            if not has_global_decl:
                                findings.append({
                                    "rule_name": "variable_shadowing",
                                    "line": line,
                                    "message": f"AST Node: Local variable '{name}' shadows a built-in or global variable on line {line}"
                                })

        ShadowingVisitor().visit(tree)
        return findings

    def _check_mutation_during_iteration(self, tree) -> List[Dict[str, Any]]:
        findings = []
        class MutationVisitor(ast.NodeVisitor):
            def visit_For(self, node):
                iterable_name = ""
                if isinstance(node.iter, ast.Name):
                    iterable_name = node.iter.id
                elif isinstance(node.iter, ast.Attribute) and isinstance(node.iter.value, ast.Name):
                    iterable_name = f"{node.iter.value.id}.{node.iter.attr}"

                if iterable_name:
                    for body_node in ast.walk(ast.Module(body=node.body, type_ignores=[])):
                        if isinstance(body_node, ast.Call) and isinstance(body_node.func, ast.Attribute):
                            caller_name = self._resolve_attribute_name(body_node.func.value)
                            if caller_name == iterable_name:
                                if body_node.func.attr in ("remove", "append", "extend", "pop", "clear", "insert"):
                                    findings.append({
                                        "rule_name": "mutation_during_iteration",
                                        "line": body_node.lineno,
                                        "message": f"AST Node: loop variable '{iterable_name}' mutated on line {body_node.lineno}"
                                    })
                self.generic_visit(node)

            def _resolve_attribute_name(self, node) -> str:
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    val = self._resolve_attribute_name(node.value)
                    if val:
                        return f"{val}.{node.attr}"
                return ""

        MutationVisitor().visit(tree)
        return findings

    def _check_unsafe_global_mutation(self, tree) -> List[Dict[str, Any]]:
        findings = []
        class GlobalMutationVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                self._check_global_mutation(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self._check_global_mutation(node)
                self.generic_visit(node)

            def _check_global_mutation(self, node):
                global_names = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        for name in child.names:
                            global_names.add(name)
                
                if global_names:
                    for child in ast.walk(node):
                        assigned_names = []
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Name):
                                    assigned_names.append((target.id, child.lineno))
                        elif isinstance(child, ast.AnnAssign):
                            if isinstance(child.target, ast.Name):
                                assigned_names.append((child.target.id, child.lineno))
                        
                        for name, line in assigned_names:
                            if name in global_names:
                                findings.append({
                                    "rule_name": "unsafe_global_mutation",
                                    "line": line,
                                    "message": f"AST Node: Unsafe mutation of global variable '{name}' on line {line}"
                                })

        GlobalMutationVisitor().visit(tree)
        return findings

    def _check_recursion_risk(self, tree) -> List[Dict[str, Any]]:
        findings = []
        class RecursionVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                self._check_recursion(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self._check_recursion(node)
                self.generic_visit(node)

            def _check_recursion(self, node):
                has_self_call = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == node.name:
                        has_self_call = True
                        break
                
                if has_self_call:
                    has_conditional = any(isinstance(child, ast.If) for child in ast.walk(node))
                    if not has_conditional:
                        findings.append({
                            "rule_name": "recursion_risk",
                            "line": node.lineno,
                            "message": f"AST Node: Recursive function '{node.name}' lacks a structural termination condition on line {node.lineno}"
                        })
        RecursionVisitor().visit(tree)
        return findings

    def _check_async_misuse(self, tree) -> List[Dict[str, Any]]:
        findings = []
        async_funcs = set()
        for child in ast.walk(tree):
            if isinstance(child, ast.AsyncFunctionDef):
                async_funcs.add(child.name)

        class AsyncVisitor(ast.NodeVisitor):
            def visit_AsyncFunctionDef(self, node):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                            if child.func.value.id == "time" and child.func.attr == "sleep":
                                findings.append({
                                    "rule_name": "async_misuse",
                                    "line": child.lineno,
                                    "message": f"AST Node: Blocking synchronous call 'time.sleep' inside async function '{node.name}' on line {child.lineno}"
                                })
                            elif child.func.value.id == "requests" and child.func.attr in ("get", "post", "put", "delete", "request"):
                                findings.append({
                                    "rule_name": "async_misuse",
                                    "line": child.lineno,
                                    "message": f"AST Node: Blocking network call 'requests.{child.func.attr}' inside async function '{node.name}' on line {child.lineno}"
                                })
                self.generic_visit(node)

        class UnawaitedCallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_await = False

            def visit_Await(self, node):
                prev = self.in_await
                self.in_await = True
                self.generic_visit(node)
                self.in_await = prev

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in async_funcs:
                    if not self.in_await:
                        findings.append({
                            "rule_name": "async_misuse",
                            "line": node.lineno,
                            "message": f"AST Node: Async function '{node.func.id}' called but not awaited on line {node.lineno}"
                        })
                self.generic_visit(node)

        AsyncVisitor().visit(tree)
        UnawaitedCallVisitor().visit(tree)
        return findings
