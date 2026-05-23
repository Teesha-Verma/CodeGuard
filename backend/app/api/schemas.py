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

class FileReport(BaseModel):
    file_path: str = Field(..., description="Path to the reviewed file")
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of detected issues in this file")
    ast_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted AST structural metadata")
    ast_summary: Optional[Dict[str, Any]] = Field(None, description="Summarized AST metadata")
    linter_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Raw linter findings for this file")

class ReviewReport(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    file_reports: List[FileReport] = Field(default_factory=list, description="List of file reports")
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Aggregated statistics of the review")
    evaluation_metrics: Optional[Dict[str, Any]] = Field(None, description="Evaluation metrics (if ground truth is available or for benchmark comparisons)")
    trace_id: str = Field(..., description="Trace identifier for logs")

class ReviewStatusResponse(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    status: str = Field(..., description="Current status of the pipeline")
    message: str = Field(..., description="Status message")
