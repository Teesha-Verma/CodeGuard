from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull request number")
    verbose_ast: bool = Field(False, description="Return full AST metadata instead of summary")

class SnippetReviewRequest(BaseModel):
    code: str = Field(..., description="Raw code snippet to review")
    language: str = Field("python", description="Language of the code snippet")
    filename: str = Field("snippet.py", description="Virtual filename for context")
    verbose_ast: bool = Field(False, description="Return full AST metadata instead of summary")

class ReviewIssue(BaseModel):
    line: int = Field(..., description="Line number where the issue was found")
    severity: str = Field(..., description="Severity of the issue")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    issue: str = Field(..., description="Short description of the issue")
    root_cause: str = Field(..., description="Detailed explanation of the root cause")
    trigger_condition: str = Field(..., description="Condition under which this issue triggers")
    fix: str = Field(..., description="Suggested fix or action")
    patch: Optional[str] = Field(None, description="Suggested code patch")
    issue_type: str = Field(..., description="Category of the issue")
    sources: List[str] = Field(default_factory=list, description="Source tools identifying findings")
    reasoning_trace: List[str] = Field(default_factory=list, description="Tracing pipeline reasoning elements")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Structured deterministic grounding packages")
    signal_priority: str = Field("medium", description="Signal priority level (high, medium, low)")
    issue_category: str = Field("runtime logic risks", description="Safety-critical issue category")
    is_low_signal: bool = Field(False, description="Whether the issue is a low-signal or style-only warning")
    detection_source: str = Field("ast", description="Source tool that detected the deterministic finding")
    reasoning_source: str = Field("static_analysis", description="Engine providing reasoning explanation")
    priority_score: float = Field(0.50, description="Unified priority score (0.0 to 1.0)")
    detection_sources: List[str] = Field(default_factory=list, description="List of detection tools/sources")

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        is_style_or_suppressed = self.is_low_signal or self.confidence < 0.3
        
        import os
        from app.core.config import get_settings
        settings = get_settings()
        verbose_style_env = os.environ.get("VERBOSE_STYLE")
        if verbose_style_env is not None:
            verbose_style = verbose_style_env.lower() == "true"
        else:
            verbose_style = settings.DEBUG
        
        if is_style_or_suppressed and not verbose_style:
            # Strip verbose fields for style-only and suppressed findings to optimize payload sizes
            for field in ["root_cause", "trigger_condition", "fix", "patch", "evidence", "sources", "detection_sources"]:
                if field in data:
                    data.pop(field)
            # Expose only a condensed reasoning trace or omit entirely
            if "reasoning_trace" in data:
                original_trace = data["reasoning_trace"]
                if original_trace:
                    data["reasoning_trace"] = [original_trace[-1]]
                else:
                    data["reasoning_trace"] = ["Static analysis explanation generated."]
        return data

    def model_dump_json(self, *args, **kwargs):
        import json
        return json.dumps(self.model_dump(*args, **kwargs))

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class FileReport(BaseModel):
    file_path: str = Field(..., description="Path to the reviewed file")
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of all detected issues in this file")
    meaningful_issues: List[ReviewIssue] = Field(default_factory=list, description="List of high-confidence, safety-critical issues")
    style_findings: List[ReviewIssue] = Field(default_factory=list, description="List of low-signal or style-only findings")
    suppressed_findings: List[ReviewIssue] = Field(default_factory=list, description="List of contextually suppressed or extremely low confidence findings")
    ast_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted AST structural metadata")
    ast_summary: Optional[Dict[str, Any]] = Field(None, description="Summarized AST metadata")
    linter_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Raw linter findings for this file")

    def __init__(self, **data):
        super().__init__(**data)
        # Automatically split findings if issues is populated but sub-lists are empty
        if self.issues and not (self.meaningful_issues or self.style_findings or self.suppressed_findings):
            raw_issues = self.issues
            self.meaningful_issues = []
            self.style_findings = []
            self.suppressed_findings = []
            for issue in raw_issues:
                if issue.confidence < 0.3:
                    self.suppressed_findings.append(issue)
                elif issue.is_low_signal:
                    self.style_findings.append(issue)
                else:
                    self.meaningful_issues.append(issue)
            # Enforce strict V1 behavior: issues field ONLY contains meaningful safety-critical findings
            self.issues = self.meaningful_issues

class ReviewReport(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    file_reports: List[FileReport] = Field(default_factory=list, description="List of file reports")
    meaningful_issues: List[ReviewIssue] = Field(default_factory=list, description="Aggregated high-confidence, safety-critical issues across files")
    style_findings: List[ReviewIssue] = Field(default_factory=list, description="Aggregated low-signal or style-only findings across files")
    suppressed_findings: List[ReviewIssue] = Field(default_factory=list, description="Aggregated contextually suppressed findings across files")
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Aggregated statistics of the review")
    evaluation_metrics: Optional[Dict[str, Any]] = Field(None, description="Evaluation metrics (if ground truth is available or for benchmark comparisons)")
    trace_id: str = Field(..., description="Trace identifier for logs")

    def __init__(self, **data):
        super().__init__(**data)
        # Automatically aggregate across all file reports
        if self.file_reports and not (self.meaningful_issues or self.style_findings or self.suppressed_findings):
            self.meaningful_issues = []
            self.style_findings = []
            self.suppressed_findings = []
            for report in self.file_reports:
                self.meaningful_issues.extend(report.meaningful_issues)
                self.style_findings.extend(report.style_findings)
                self.suppressed_findings.extend(report.suppressed_findings)

class ReviewStatusResponse(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    status: str = Field(..., description="Current status of the pipeline")
    message: str = Field(..., description="Status message")
