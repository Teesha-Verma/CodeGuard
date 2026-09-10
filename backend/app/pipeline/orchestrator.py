import os
import time
import ast
from typing import List, Dict, Any, Optional

from app.api.schemas import FileReport
from app.core.logger import PipelineLogger
from app.diff.diff_parser import DiffFile, DiffParser
from app.diff.context_builder import ContextBuilder

# Upgraded Static Analysis
from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.complexity_analyzer import ComplexityAnalyzer
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.mutation_detector import MutationDetector
from app.static_analysis.import_analyzer import ImportAnalyzer
from app.static_analysis.heuristic_engine import HeuristicEngine

# Deep Graph & Taint Analysis
from app.analysis.cfg.cfg_builder import CFGBuilder
from app.analysis.call_graph.call_graph_builder import CallGraphBuilder
from app.analysis.dataflow.taint.taint_engine import TaintEngine
from app.analysis.dataflow.taint.vulnerability_rules import VulnerabilityRules
from app.analysis.repository.query_engine import RepositoryQueryEngine

# Linters
from app.linters.pylint_runner import PylintRunner
from app.linters.flake8_runner import Flake8Runner
from app.linters.bandit_runner import BanditRunner

# Core Aggregation & Generation
from app.pipeline.feature_aggregator import FeatureAggregator
from app.reasoning.review_generator import ReviewGenerator


class PipelineOrchestrator:
    """Main pipeline orchestrator coordinating deterministic static analysis, deep graph & taint flows, RAG knowledge, and grounded LLM reasoning."""

    def __init__(self, review_id: str):
        self.review_id = review_id
        self.logger = PipelineLogger(review_id=review_id, stage="orchestrator")
        self.traces: List[Dict[str, Any]] = []

        # Static Analysis Tools
        self.ast_parser = PythonASTParser()
        self.complexity = ComplexityAnalyzer()
        self.scope = ScopeTracker()
        self.mutation_detector = MutationDetector()
        self.import_analyzer = ImportAnalyzer()
        self.heuristic_engine = HeuristicEngine()

        # Deep Graph & Flow Analyzers
        self.call_graph_builder = CallGraphBuilder()

        # Linters
        self.linters = [PylintRunner(), Flake8Runner(), BanditRunner()]

        # Grounded Pipelines
        self.aggregator = FeatureAggregator()
        self.review_generator = ReviewGenerator(review_id)

    def process_file(
        self,
        diff_file: DiffFile,
        repo_path: str,
        repo_intelligence: Optional[Dict[str, Any]] = None,
        sources_cache: Optional[Dict[str, str]] = None,
        supporting_context: Optional[Dict[str, Any]] = None,
        pr_changed_files: Optional[List[str]] = None,
        verbose_ast: bool = False
    ) -> FileReport:
        """Processes a single file through the complete analysis and reasoning pipeline."""
        self.logger.info(f"Processing file: {diff_file.file_path}")

        # Check deleted status or non-python file
        if diff_file.is_deleted or not diff_file.file_path.endswith(".py"):
            return FileReport(file_path=diff_file.file_path)

        # Enforce strict PR-analysis scope
        norm_file_path = DiffParser.normalize_path(diff_file.file_path)
        if pr_changed_files:
            norm_pr_set = {DiffParser.normalize_path(p) for p in pr_changed_files if p}
            if norm_pr_set and norm_file_path not in norm_pr_set:
                self.logger.info(f"Skipping {diff_file.file_path} — outside PR analysis scope.")
                return FileReport(file_path=diff_file.file_path)

        file_path_abs = os.path.join(repo_path, diff_file.file_path)

        if not os.path.exists(file_path_abs):
            return FileReport(file_path=diff_file.file_path)

        try:
            with open(file_path_abs, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {diff_file.file_path}: {e}")
            return FileReport(file_path=diff_file.file_path)

        # 1. Context Building (getting raw code snippets around modified lines)
        context_builder = ContextBuilder(repo_path)
        context = context_builder.build_context(diff_file)

        # 2. Deterministic AST Static Analysis
        ast_start = time.perf_counter()
        ast_meta = self.ast_parser.parse(code_content, diff_file.added_lines)
        ast_duration = (time.perf_counter() - ast_start) * 1000

        self.traces.append({
            "stage": "ast_parsing",
            "duration_ms": ast_duration,
            "input_data": {
                "file_path": diff_file.file_path,
                "added_lines": diff_file.added_lines
            },
            "output_data": {
                "rules_executed": [
                    "eval_detection", "exec_detection", "unsafe_subprocess", "unsafe_pickle",
                    "nested_loop", "variable_shadowing", "mutation_during_iteration",
                    "unsafe_global_mutation", "recursion_risk", "async_misuse"
                ],
                "findings": ast_meta.get("ast_rules_findings", []),
                "async_issues": ast_meta.get("async_issues", [])
            }
        })

        comp = self.complexity.analyze(code_content, diff_file.file_path)
        scope_issues = self.scope.analyze(code_content)
        mutation_issues = self.mutation_detector.analyze(code_content)
        import_issues = self.import_analyzer.analyze(code_content)
        heuristic_issues = self.heuristic_engine.analyze(code_content)
        control_structures = ast_meta.get("control_structures", [])

        # 3. Control Flow Graph (CFG) Construction
        cfg_start = time.perf_counter()
        cfg_data: Dict[str, Any] = {}
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cfg_builder = CFGBuilder()
                    cfg_graph = cfg_builder.build(node)
                    cfg_data[node.name] = {
                        "blocks_count": len(cfg_graph.nodes),
                        "edges_count": len(cfg_graph.edges),
                        "has_cycles": cfg_graph.has_cycle(),
                        "complexity": cfg_graph.get_cyclomatic_complexity(),
                        "line": node.lineno
                    }
        except Exception as cfg_err:
            self.logger.debug(f"CFG extraction skipped for {diff_file.file_path}: {cfg_err}")
        cfg_duration = (time.perf_counter() - cfg_start) * 1000

        self.traces.append({
            "stage": "cfg_construction",
            "duration_ms": cfg_duration,
            "input_data": {"file_path": diff_file.file_path},
            "output_data": {"functions_analyzed": len(cfg_data), "cfg_summary": cfg_data}
        })

        # 4. Call Graph Analysis
        cg_start = time.perf_counter()
        call_graph_data: Dict[str, Any] = {}
        try:
            module_name = diff_file.file_path.replace(".py", "").replace("/", ".").replace("\\", ".")
            cg = self.call_graph_builder.build({module_name: code_content}, {module_name: file_path_abs})
            call_graph_data = {
                "nodes_count": len(cg.nodes),
                "edges_count": len(cg.edges),
                "calls": [
                    {"caller": edge.source, "callee": edge.target, "line": edge.call_site_line}
                    for edge in cg.edges
                ]
            }
        except Exception as cg_err:
            self.logger.debug(f"Call graph analysis skipped for {diff_file.file_path}: {cg_err}")
        cg_duration = (time.perf_counter() - cg_start) * 1000

        self.traces.append({
            "stage": "call_graph_analysis",
            "duration_ms": cg_duration,
            "input_data": {"file_path": diff_file.file_path},
            "output_data": call_graph_data
        })

        # 5. Data Flow / Taint Analysis
        df_start = time.perf_counter()
        dataflow_findings: List[Dict[str, Any]] = []
        try:
            module_name = diff_file.file_path.replace(".py", "").replace("/", ".").replace("\\", ".")
            taint_engine = TaintEngine()
            taint_engine.add_module(module_name, code_content, file_path=file_path_abs)
            flow_paths = taint_engine.run()
            if flow_paths and taint_engine.merged_graph:
                vuln_rules = VulnerabilityRules(graph=taint_engine.merged_graph)
                vulns = vuln_rules.evaluate(flow_paths)
                for v in vulns:
                    dataflow_findings.append(v.to_dict())
        except Exception as df_err:
            self.logger.debug(f"Data flow analysis skipped for {diff_file.file_path}: {df_err}")
        df_duration = (time.perf_counter() - df_start) * 1000

        self.traces.append({
            "stage": "dataflow_analysis",
            "duration_ms": df_duration,
            "input_data": {"file_path": diff_file.file_path},
            "output_data": {"flows_detected": len(dataflow_findings), "findings": dataflow_findings}
        })

        # 6. Repository Intelligence Analysis
        repo_start = time.perf_counter()
        repo_intel: Dict[str, Any] = repo_intelligence or {}
        if not repo_intel:
            try:
                sources = sources_cache or {norm_file_path: code_content}
                if sources:
                    query_engine = RepositoryQueryEngine(sources=sources, changed_files=[diff_file.file_path])
                    repo_intel = {
                        "architecture": [a.to_dict() for a in query_engine.find_architecture()],
                        "hotspots": [h.to_dict() for h in query_engine.find_hotspots(top_n=3)],
                        "change_impact": query_engine.find_change_impact().to_dict() if query_engine.find_change_impact() else {},
                    }
            except Exception as repo_err:
                self.logger.debug(f"Repository intelligence skipped for {diff_file.file_path}: {repo_err}")
        repo_duration = (time.perf_counter() - repo_start) * 1000

        self.traces.append({
            "stage": "repository_intelligence",
            "duration_ms": repo_duration,
            "input_data": {"repo_path": repo_path, "changed_file": diff_file.file_path},
            "output_data": repo_intel
        })

        # 7. Linter Execution
        linter_start = time.perf_counter()
        linter_findings = []
        for linter in self.linters:
            linter_findings.extend(linter.run(file_path_abs))

        changed_lines_set = set(diff_file.added_lines)
        relevant_linters = [f for f in linter_findings if f.line in changed_lines_set]
        linter_duration = (time.perf_counter() - linter_start) * 1000

        self.traces.append({
            "stage": "linter_execution",
            "duration_ms": linter_duration,
            "input_data": {"file_path": diff_file.file_path},
            "output_data": {"findings_count": len(relevant_linters)}
        })

        # 8. Feature Aggregation (bundling into grounded context payload)
        aggregated = self.aggregator.aggregate(
            diff_file=diff_file,
            context_snippets=context.get("snippets", []),
            ast_metadata=ast_meta,
            complexity=comp,
            scope_data=scope_issues,
            control_flow=control_structures,
            import_data=import_issues,
            mutation_data=mutation_issues,
            linter_findings=relevant_linters,
            heuristic_findings=heuristic_issues,
            cfg_data=cfg_data,
            call_graph_data=call_graph_data,
            dataflow_findings=dataflow_findings,
            repo_intelligence=repo_intel,
            code_content=code_content,
            pr_changed_files=pr_changed_files,
            supporting_context=supporting_context,
        )

        # 9. Grounded Review Issue Generation with RAG Knowledge
        final_issues = self.review_generator.generate(aggregated)
        for issue in final_issues:
            issue.file_path = diff_file.file_path
        self.traces.extend(self.review_generator.traces)

        dangerous_patterns_count = sum(
            1 for issue in final_issues
            if (
                issue.issue_category in ("security", "mutation risks", "async misuse")
                and issue.confidence >= 0.3
            )
        )

        summary = {
            "function_count": len(ast_meta.get("functions", [])),
            "class_count": len(ast_meta.get("classes", [])),
            "dangerous_patterns": dangerous_patterns_count,
            "dataflow_taint_count": len(dataflow_findings),
            "cfg_functions_count": len(cfg_data),
        }

        return FileReport(
            file_path=diff_file.file_path,
            issues=final_issues,
            ast_metadata={
                "functions": ast_meta.get("functions", []),
                "classes": ast_meta.get("classes", []),
                "complexity": comp,
                "dangerous_calls": import_issues.get("dangerous_imports", []),
                "cfg_analysis": cfg_data,
                "dataflow_findings": dataflow_findings,
            } if verbose_ast else None,
            ast_summary=summary,
            linter_findings=[{
                "rule": f.rule_id,
                "message": f.message,
                "line": f.line,
                "tool": f.tool_name
            } for f in relevant_linters],
            file_content=code_content
        )
