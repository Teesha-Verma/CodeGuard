import os
from typing import List, Dict, Any
from app.api.schemas import ReviewRequest, SnippetReviewRequest, ReviewReport, FileReport, ReviewIssue
from app.core.logger import PipelineLogger
from app.core.constants import IssueSource, Severity

from app.diff.diff_parser import DiffParser, DiffFile
from app.diff.context_builder import ContextBuilder

from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.complexity_analyzer import ComplexityAnalyzer
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.control_flow import ControlFlowAnalyzer
from app.static_analysis.dependency_analyzer import DependencyAnalyzer
from app.static_analysis.pattern_detector import PatternDetector

from app.linters.pylint_runner import PylintRunner
from app.linters.flake8_runner import Flake8Runner
from app.linters.bandit_runner import BanditRunner

from app.pipeline.feature_aggregator import FeatureAggregator
from app.agents.bug_detection_agent import BugDetectionAgent
from app.agents.root_cause_agent import RootCauseAgent
from app.agents.fix_suggestion_agent import FixSuggestionAgent

class PipelineOrchestrator:
    """Main pipeline orchestrator that coordinates all stages of the review."""
    
    def __init__(self, review_id: str):
        self.review_id = review_id
        self.logger = PipelineLogger(review_id=review_id, stage="orchestrator")
        
        # Tools
        self.diff_parser = DiffParser()
        self.ast_parser = PythonASTParser()
        self.complexity = ComplexityAnalyzer()
        self.scope = ScopeTracker()
        self.control_flow = ControlFlowAnalyzer()
        self.dependencies = DependencyAnalyzer()
        self.patterns = PatternDetector()
        
        # Linters
        self.linters = [PylintRunner(), Flake8Runner(), BanditRunner()]
        
        # Agents
        self.aggregator = FeatureAggregator()
        self.bug_agent = BugDetectionAgent(review_id)
        self.root_cause_agent = RootCauseAgent(review_id)
        self.fix_agent = FixSuggestionAgent(review_id)
        
    def process_file(self, diff_file: DiffFile, repo_path: str) -> FileReport:
        """Processes a single file through the analysis and reasoning pipeline."""
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
            
        # 1. Context Building
        context_builder = ContextBuilder(repo_path)
        context = context_builder.build_context(diff_file)
        
        # 2. Static Analysis
        ast_meta = self.ast_parser.parse(code_content, diff_file.added_lines)
        comp = self.complexity.analyze(code_content)
        scope = self.scope.analyze(code_content)
        cf = self.control_flow.analyze(code_content)
        deps = self.dependencies.analyze(code_content)
        pats = self.patterns.analyze(code_content)
        
        # 3. Linters
        linter_findings = []
        for linter in self.linters:
            linter_findings.extend(linter.run(file_path_abs))
            
        # Filter linter findings to changed lines
        changed_lines_set = set(diff_file.added_lines)
        relevant_linters = [f for f in linter_findings if f.line in changed_lines_set]
        
        # 4. Aggregation
        aggregated = self.aggregator.aggregate(
            diff_file, context.get("snippets", []), ast_meta, comp, scope, cf, deps, pats, relevant_linters
        )
        
        # 5. LLM Agents
        raw_issues = self.bug_agent.detect(aggregated)
        
        final_issues = []
        for raw in raw_issues:
            rc = self.root_cause_agent.analyze(raw, aggregated)
            fix = self.fix_agent.suggest(raw, rc, aggregated)
            
            final_issues.append(ReviewIssue(
                line=raw["line"],
                severity=raw["severity"],
                confidence=raw["confidence"],
                issue=raw["issue"],
                root_cause=rc,
                fix=fix["fix"],
                patch=fix["patch"],
                issue_type=raw["issue_type"],
                source=IssueSource.LLM
            ))
            
        return FileReport(
            file_path=diff_file.file_path,
            issues=final_issues,
            ast_metadata={"functions": ast_meta, "complexity": comp},
            linter_findings=[{"rule": f.rule_id, "message": f.message, "line": f.line, "tool": f.tool_name} for f in relevant_linters]
        )
