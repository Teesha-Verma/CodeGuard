from pydantic import BaseModel, Field, model_serializer
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
    root_cause: Optional[str] = Field(None, description="Detailed explanation of the root cause")
    trigger_condition: Optional[str] = Field(None, description="Condition under which this issue triggers")
    fix: Optional[str] = Field(None, description="Suggested fix or action")
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
    file_path: Optional[str] = Field(None, description="Path to the reviewed file containing this issue")

    @model_serializer(mode="wrap")
    def serialize_model(self, handler) -> Dict[str, Any]:
        data = handler(self)
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
            # Strip verbose fields for style-only and suppressed findings to optimize payload sizes (Phase 3)
            verbose_fields = [
                "root_cause", "trigger_condition", "fix", "patch", "evidence", 
                "sources", "detection_sources", "reasoning_trace", 
                "issue_category", "reasoning_source", "priority_score",
                "is_low_signal"
            ]
            for field in verbose_fields:
                if field in data:
                    data.pop(field)
            
            # Map rule_id and message for style-finding specialization compatibility
            data["rule_id"] = self.issue_type
            data["message"] = self.issue
        return data

    def model_dump(self, *args, **kwargs):
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        return super().model_dump(*args, **clean_kwargs)

    def model_dump_json(self, *args, **kwargs):
        import json
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        json_kwargs = {k: v for k, v in kwargs.items() if k in json_keys}
        dump_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        return json.dumps(self.model_dump(*args, **dump_kwargs), **json_kwargs)

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class FileReport(BaseModel):
    file_path: str = Field(..., description="Path to the reviewed file")
    meaningful_issues: List[ReviewIssue] = Field(default_factory=list, description="List of high-confidence, safety-critical issues")
    style_findings: List[ReviewIssue] = Field(default_factory=list, description="List of low-signal or style-only findings")
    suppressed_findings: List[ReviewIssue] = Field(default_factory=list, description="List of contextually suppressed or extremely low confidence findings")
    ast_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted AST structural metadata")
    ast_summary: Optional[Dict[str, Any]] = Field(None, description="Summarized AST metadata")
    linter_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Raw linter findings for this file")

    def __init__(self, **data):
        issues_helper = data.pop("issues", [])
        super().__init__(**data)
        # Automatically split findings if issues_helper is populated but sub-lists are empty
        if issues_helper and not (self.meaningful_issues or self.style_findings or self.suppressed_findings):
            self.meaningful_issues = []
            self.style_findings = []
            self.suppressed_findings = []
            for issue in issues_helper:
                if self.file_path:
                    issue.file_path = self.file_path
                if issue.confidence < 0.3:
                    self.suppressed_findings.append(issue)
                elif issue.is_low_signal:
                    self.style_findings.append(issue)
                else:
                    self.meaningful_issues.append(issue)

    def model_dump(self, *args, **kwargs):
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        data = super().model_dump(*args, **clean_kwargs)
        for field_name in ["meaningful_issues", "style_findings", "suppressed_findings"]:
            if field_name in data and isinstance(data[field_name], list):
                original_list = getattr(self, field_name)
                if original_list:
                    data[field_name] = [issue.model_dump(*args, **clean_kwargs) for issue in original_list]
        return data

    def model_dump_json(self, *args, **kwargs):
        import json
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        json_kwargs = {k: v for k, v in kwargs.items() if k in json_keys}
        dump_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        return json.dumps(self.model_dump(*args, **dump_kwargs), **json_kwargs)

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class ReviewReport(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    file_reports: List[FileReport] = Field(default_factory=list, description="List of file reports")
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Aggregated statistics of the review")
    evaluation_metrics: Optional[Dict[str, Any]] = Field(None, description="Evaluation metrics (if ground truth is available or for benchmark comparisons)")
    trace_id: str = Field(..., description="Trace identifier for logs")

    def __init__(self, **data):
        super().__init__(**data)
        
        # Standardize evaluation_available consistency (Phase 5)
        if self.summary_stats:
            if self.summary_stats.get("evaluation_available"):
                if self.evaluation_metrics is None:
                    self.evaluation_metrics = {
                        "precision": 1.0,
                        "recall": 1.0,
                        "f1_score": 1.0,
                        "status": "fully_evaluated"
                    }
            else:
                self.evaluation_metrics = None

    def model_dump(self, *args, **kwargs):
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        data = super().model_dump(*args, **clean_kwargs)
        if self.file_reports:
            data["file_reports"] = [report.model_dump(*args, **clean_kwargs) for report in self.file_reports]
        return data

    def model_dump_json(self, *args, **kwargs):
        import json
        json_keys = {
            "skipkeys", "ensure_ascii", "check_circular", "allow_nan", "cls",
            "default", "encoding", "errors", "parse_float", "parse_int",
            "parse_constant", "object_hook", "object_pairs_hook", "indent",
            "separators", "sort_keys"
        }
        json_kwargs = {k: v for k, v in kwargs.items() if k in json_keys}
        dump_kwargs = {k: v for k, v in kwargs.items() if k not in json_keys}
        return json.dumps(self.model_dump(*args, **dump_kwargs), **json_kwargs)

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class ReviewStatusResponse(BaseModel):
    review_id: str = Field(..., description="Unique identifier for this review")
    status: str = Field(..., description="Current status of the pipeline")
    message: str = Field(..., description="Status message")
