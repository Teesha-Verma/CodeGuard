from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.core.constants import Severity, IssueType, IssueSource

class ReviewRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull request number")

class SnippetReviewRequest(BaseModel):
    code: str = Field(..., description="Raw code snippet to review")
    language: str = Field("python", description="Language of the code snippet")
    filename: str = Field("snippet.py", description="Virtual filename for context")

class ReviewIssue(BaseModel):
    line: int = Field(..., description="Line number where the issue was found")
    severity: Severity = Field(..., description="Severity of the issue")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    issue: str = Field(..., description="Short description of the issue")
    root_cause: str = Field(..., description="Detailed explanation of the root cause")
    fix: str = Field(..., description="Suggested fix or action")
    patch: Optional[str] = Field(None, description="Suggested code patch")
    issue_type: IssueType = Field(..., description="Category of the issue")
    source: IssueSource = Field(..., description="Source of the finding (Linter, LLM, etc.)")

class FileReport(BaseModel):
    file_path: str = Field(..., description="Path to the reviewed file")
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of detected issues in this file")
    ast_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted AST structural metadata")
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
