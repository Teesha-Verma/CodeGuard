import os
from typing import List, Dict, Any
from app.api.schemas import FileReport
from app.core.logger import PipelineLogger

from app.diff.diff_parser import DiffFile
from app.diff.context_builder import ContextBuilder

# Upgraded Static Analysis
from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.complexity_analyzer import ComplexityAnalyzer
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.mutation_detector import MutationDetector
from app.static_analysis.import_analyzer import ImportAnalyzer
from app.static_analysis.heuristic_engine import HeuristicEngine

# Linters
from app.linters.pylint_runner import PylintRunner
from app.linters.flake8_runner import Flake8Runner
from app.linters.bandit_runner import BanditRunner

# Core Aggregation & Generation
from app.pipeline.feature_aggregator import FeatureAggregator
from app.reasoning.review_generator import ReviewGenerator

class PipelineOrchestrator:
    """Main pipeline orchestrator coordinating deterministic static analysis with grounded LLM reasoning."""
    
    def __init__(self, review_id: str):
        self.review_id = review_id
        self.logger = PipelineLogger(review_id=review_id, stage="orchestrator")
        self.traces = []
        
        # Static Analysis Tools
        self.ast_parser = PythonASTParser()
        self.complexity = ComplexityAnalyzer()
        self.scope = ScopeTracker()
        self.mutation_detector = MutationDetector()
        self.import_analyzer = ImportAnalyzer()
        self.heuristic_engine = HeuristicEngine()
        
        # Linters
        self.linters = [PylintRunner(), Flake8Runner(), BanditRunner()]
        
        # Grounded Pipelines
        self.aggregator = FeatureAggregator()
        self.review_generator = ReviewGenerator(review_id)
        
    def process_file(self, diff_file: DiffFile, repo_path: str, verbose_ast: bool = False) -> FileReport:
        """Processes a single file through the analysis and reasoning pipeline."""
        import time
        self.logger.info(f"Processing file: {diff_file.file_path}")
        
        file_path_abs = os.path.join(repo_path, diff_file.file_path)
        
        if not os.path.exists(file_path_abs) or not diff_file.file_path.endswith(".py"):
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
        
        # 2. Deterministic Static Analysis
        ast_start = time.perf_counter()
        ast_meta = self.ast_parser.parse(code_content, diff_file.added_lines)
        ast_duration = (time.perf_counter() - ast_start) * 1000
        
        # Record AST trace
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
        
        # Create control flow list (using loops extracted from control_structures)
        control_structures = ast_meta.get("control_structures", [])
        
        # 3. Linter Execution
        linter_findings = []
        for linter in self.linters:
            linter_findings.extend(linter.run(file_path_abs))
            
        # Filter linter findings strictly to added/changed lines
        changed_lines_set = set(diff_file.added_lines)
        relevant_linters = [f for f in linter_findings if f.line in changed_lines_set]
        
        # 4. Feature Aggregation (bundling into grounded context payload)
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
            heuristic_findings=heuristic_issues
        )
        
        # 5. Grounded Review Issue Generation
        final_issues = self.review_generator.generate(aggregated)
        
        # Collect traces from generator
        self.traces.extend(self.review_generator.traces)
        
        # Count only validated, surfaced, and evidence-backed dangerous/safety-critical findings
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
            "dangerous_patterns": dangerous_patterns_count
        }

        # Verbose AST metadata appears ONLY when requested, or debug/developer mode is enabled
        from app.core.config import get_settings
        settings = get_settings()
        debug_or_dev_enabled = (
            settings.DEBUG 
            or os.environ.get("DEVELOPER_MODE", "").lower() == "true"
            or os.environ.get("DEBUG_MODE", "").lower() == "true"
        )
        verbose_final = verbose_ast or debug_or_dev_enabled

        return FileReport(
            file_path=diff_file.file_path,
            issues=final_issues,
            ast_metadata={
                "functions": ast_meta.get("functions", []),
                "classes": ast_meta.get("classes", []),
                "complexity": comp,
                "dangerous_calls": import_issues.get("dangerous_imports", [])
            } if verbose_final else None,
            ast_summary=summary,
            linter_findings=[{
                "rule": f.rule_id,
                "message": f.message,
                "line": f.line,
                "tool": f.tool_name
            } for f in relevant_linters]
        )
