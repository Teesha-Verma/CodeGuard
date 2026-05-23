import ast
import logging
from typing import List, Dict, Any
from app.core.config import get_settings

class HeuristicEngine:
    """
    Deterministic rule-based analysis engine.
    Detects structural candidate issues directly from Python AST.
    """
    def __init__(self):
        self.logger = logging.getLogger("codeguard.heuristic_engine")
        self.settings = get_settings()

    def _run_rule(self, name: str, func, *args, **kwargs) -> List[Dict[str, Any]]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Heuristic rule {name} failed: {e}")
            return []

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(code)
        except (SyntaxError, IndentationError):
            return []

        findings = []
        findings.extend(self._run_rule("mutation_during_iteration", self._check_mutation_during_iteration, tree))
        findings.extend(self._run_rule("mutable_defaults", self._check_mutable_defaults, tree))
        findings.extend(self._run_rule("broad_except", self._check_broad_except, tree))
        findings.extend(self._run_rule("dangerous_execution", self._check_dangerous_execution, tree))
        findings.extend(self._run_rule("recursive_risk", self._check_recursive_risk, tree))
        findings.extend(self._run_rule("excessive_nesting", self._check_excessive_nesting, tree))
        findings.extend(self._run_rule("async_misuse", self._check_async_misuse, tree))
        findings.extend(self._run_rule("global_mutation", self._check_global_mutation, tree))
        return findings

    # -- Checker 1: Mutation during active iteration loops
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
                                        "message": f"AST Node: loop variable '{iterable_name}' mutated on line {body_node.lineno}",
                                        "evidence_strength": 1.0,
                                        "severity": "critical",
                                        "issue_type": "runtime_logic_error"
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

    # -- Checker 2: Mutable default arguments (e.g. def f(x=[]))
    def _check_mutable_defaults(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        findings.append({
                            "rule_name": "mutable_default",
                            "line": node.lineno,
                            "message": f"Mutable default argument in function '{node.name}'",
                            "evidence_strength": 1.0,
                            "severity": "high",
                            "issue_type": "runtime_logic_error"
                        })
        return findings

    # -- Checker 3: Broad exception swallowing (e.g. except Exception: pass or except: pass)
    def _check_broad_except(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    is_broad = False
                    if handler.type is None:
                        is_broad = True
                    elif isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException"):
                        is_broad = True
                    
                    if is_broad:
                        is_swallowing = False
                        if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                            is_swallowing = True
                        elif len(handler.body) > 0:
                            if all(isinstance(stmt, ast.Pass) for stmt in handler.body):
                                is_swallowing = True
                        
                        if is_swallowing:
                            findings.append({
                                "rule_name": "broad_except",
                                "line": handler.lineno,
                                "message": "AST Node: Broad exception swallowed with pass, masking potential errors.",
                                "evidence_strength": 0.9,
                                "severity": "medium",
                                "issue_type": "runtime_logic_error"
                            })
        return findings

    # -- Checker 4: Dangerous dynamic execution
    def _check_dangerous_execution(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    findings.append({
                        "rule_name": "dangerous_builtin",
                        "line": node.lineno,
                        "message": f"AST Node: Use of dangerous built-in '{node.func.id}'",
                        "evidence_strength": 1.0,
                        "severity": "high",
                        "issue_type": "security"
                    })
        return findings

    # -- Checker 5: Recursive Risk
    def _check_recursive_risk(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
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
                            "message": f"AST Node: Recursive function '{node.name}' lacks a structural termination condition on line {node.lineno}",
                            "evidence_strength": 0.8,
                            "severity": "high",
                            "issue_type": "runtime_logic_error"
                        })
        return findings

    # -- Checker 6: Excessive Nesting
    def _check_excessive_nesting(self, tree) -> List[Dict[str, Any]]:
        findings = []
        max_depth = self.settings.MAX_NESTING_DEPTH
        
        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                
            def visit_For(self, node):
                self.current_depth += 1
                if self.current_depth > max_depth:
                    findings.append({
                        "rule_name": "excessive_nesting",
                        "line": node.lineno,
                        "message": f"AST Node: Nesting depth ({self.current_depth}) exceeds the maximum safety limit ({max_depth})",
                        "evidence_strength": 0.7,
                        "severity": "medium",
                        "issue_type": "code_smell"
                    })
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_While(self, node):
                self.current_depth += 1
                if self.current_depth > max_depth:
                    findings.append({
                        "rule_name": "excessive_nesting",
                        "line": node.lineno,
                        "message": f"AST Node: Nesting depth ({self.current_depth}) exceeds the maximum safety limit ({max_depth})",
                        "evidence_strength": 0.7,
                        "severity": "medium",
                        "issue_type": "code_smell"
                    })
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_If(self, node):
                self.current_depth += 1
                if self.current_depth > max_depth:
                    findings.append({
                        "rule_name": "excessive_nesting",
                        "line": node.lineno,
                        "message": f"AST Node: Nesting depth ({self.current_depth}) exceeds the maximum safety limit ({max_depth})",
                        "evidence_strength": 0.7,
                        "severity": "medium",
                        "issue_type": "code_smell"
                    })
                self.generic_visit(node)
                self.current_depth -= 1

        NestingVisitor().visit(tree)
        return findings

    # -- Checker 7: Async Misuse (async without await, time.sleep inside async)
    def _check_async_misuse(self, tree) -> List[Dict[str, Any]]:
        findings = []
        async_funcs = set()
        for child in ast.walk(tree):
            if isinstance(child, ast.AsyncFunctionDef):
                async_funcs.add(child.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # async def missing await
                has_await = any(isinstance(child, ast.Await) for child in ast.walk(node))
                if not has_await:
                    findings.append({
                        "rule_name": "async_misuse",
                        "line": node.lineno,
                        "message": f"AST Node: Async function '{node.name}' does not contain any 'await' statements.",
                        "evidence_strength": 0.8,
                        "severity": "high",
                        "issue_type": "concurrency"
                    })

                # Blocking calls inside async context
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                            if child.func.value.id == "time" and child.func.attr == "sleep":
                                findings.append({
                                    "rule_name": "async_misuse",
                                    "line": child.lineno,
                                    "message": f"AST Node: Blocking synchronous call 'time.sleep' inside async function '{node.name}' on line {child.lineno}",
                                    "evidence_strength": 0.9,
                                    "severity": "high",
                                    "issue_type": "concurrency"
                                })
                            elif child.func.value.id == "requests" and child.func.attr in ("get", "post", "put", "delete", "request"):
                                findings.append({
                                    "rule_name": "async_misuse",
                                    "line": child.lineno,
                                    "message": f"AST Node: Blocking network call 'requests.{child.func.attr}' inside async function '{node.name}' on line {child.lineno}",
                                    "evidence_strength": 0.9,
                                    "severity": "high",
                                    "issue_type": "concurrency"
                                })

        # Async function called but not awaited
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
                            "message": f"AST Node: Async function '{node.func.id}' called but not awaited on line {node.lineno}",
                            "evidence_strength": 0.8,
                            "severity": "high",
                            "issue_type": "concurrency"
                        })
                self.generic_visit(node)

        UnawaitedCallVisitor().visit(tree)
        return findings

    # -- Checker 8: Shared Global State Mutation
    def _check_global_mutation(self, tree) -> List[Dict[str, Any]]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
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
                                    "rule_name": "global_modification",
                                    "line": line,
                                    "message": f"AST Node: Unsafe mutation of global variable '{name}' on line {line}",
                                    "evidence_strength": 0.8,
                                    "severity": "medium",
                                    "issue_type": "runtime_logic_error"
                                })
        return findings
