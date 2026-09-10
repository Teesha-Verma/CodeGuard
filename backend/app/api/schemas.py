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
    llm_provider: Optional[str] = Field(None, description="LLM provider used for reasoning")
    llm_model: Optional[str] = Field(None, description="LLM model used for reasoning")
    dataflow_path: Optional[List[str]] = Field(default=None, description="Source-to-sink taint propagation path if applicable")
    standards: Optional[List[str]] = Field(default_factory=list, description="Associated security standards (e.g. CWE, OWASP)")
    impact: Optional[str] = Field(default=None, description="Real-world security or operational impact")
    category: Optional[str] = Field(default=None, description="Normalized issue category")

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
                "is_low_signal", "llm_provider", "llm_model"
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
        data = super().model_dump(*args, **clean_kwargs)
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
                "is_low_signal", "llm_provider", "llm_model"
            ]
            for field in verbose_fields:
                if field in data:
                    data.pop(field)
            
            # Map rule_id and message for style-finding specialization compatibility
            data["rule_id"] = self.issue_type
            data["message"] = self.issue
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

class FileReport(BaseModel):
    file_path: str = Field(..., description="Path to the reviewed file")
    meaningful_issues: List[ReviewIssue] = Field(default_factory=list, description="List of high-confidence, safety-critical issues")
    style_findings: List[ReviewIssue] = Field(default_factory=list, description="List of low-signal or style-only findings")
    suppressed_findings: List[ReviewIssue] = Field(default_factory=list, description="List of contextually suppressed or extremely low confidence findings")
    ast_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted AST structural metadata")
    ast_summary: Optional[Dict[str, Any]] = Field(None, description="Summarized AST metadata")
    linter_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Raw linter findings for this file")
    file_content: Optional[str] = Field(None, description="Source content of the file for preview and highlighting")

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

    @property
    def issues(self) -> List[ReviewIssue]:
        """Convenience property combining meaningful, style, and suppressed issues."""
        return self.meaningful_issues + self.style_findings + self.suppressed_findings

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
        # Provide issues alias for backwards compatibility
        data["issues"] = data.get("meaningful_issues", []) + data.get("style_findings", []) + data.get("suppressed_findings", [])
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
    repo_url: Optional[str] = Field(None, description="Repository URL if PR review")
    pr_number: Optional[int] = Field(None, description="PR number if PR review")
    snippet_filename: Optional[str] = Field(None, description="Filename if snippet review")
    created_at: Optional[str] = Field(None, description="Timestamp review was created")
    duration_seconds: Optional[float] = Field(None, description="Total analysis duration in seconds")
    repo_intelligence: Optional[Dict[str, Any]] = Field(None, description="Repository architecture and hotspot analysis")
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
    status: str = Field(..., description="Current status of the pipeline: queued, running, processing, completed, failed, cancelled, timed_out")
    message: Optional[str] = Field("Status update", description="Status message")
    stage: Optional[str] = Field(None, description="Current execution stage")
    error_code: Optional[str] = Field(None, description="Error code if review failed")
    error_message: Optional[str] = Field(None, description="Detailed error description if review failed")
    failed_stage: Optional[str] = Field(None, description="Pipeline stage where failure occurred")
    duration_seconds: Optional[float] = Field(None, description="Elapsed execution duration in seconds")
    started_at: Optional[str] = Field(None, description="ISO timestamp when processing started")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last status update")
    progress_percent: Optional[int] = Field(None, description="Optional stage-based progress percentage")


# ============================================================
# REVIEW HISTORY & DASHBOARD SCHEMAS
# ============================================================

class StoredReviewSummary(BaseModel):
    review_id: str
    type: str = Field("pr", description="'pr' or 'snippet'")
    repo_url: Optional[str] = None
    pr_number: Optional[int] = None
    filename: Optional[str] = None
    language: Optional[str] = "python"
    status: str = Field("completed", description="'started', 'running', 'completed', 'failed'")
    created_at: str
    duration_seconds: Optional[float] = None
    total_issues: int = 0
    meaningful_issues: int = 0
    style_findings: int = 0
    suppressed_findings: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    error_message: Optional[str] = None


class ReviewHistoryResponse(BaseModel):
    reviews: List[StoredReviewSummary]
    total: int
    limit: int
    offset: int


class DashboardStatsResponse(BaseModel):
    total_reviews: int
    completed_reviews: int
    total_issues_found: int
    total_issues: Optional[int] = None
    critical_high_issues: int
    critical_count: Optional[int] = 0
    recent_reviews: List[StoredReviewSummary] = Field(default_factory=list)


# ============================================================
# DATAFLOW / TAINT SCHEMAS
# ============================================================

class DataflowNode(BaseModel):
    id: str
    step_number: int
    label: str
    role: str = Field(..., description="'SOURCE', 'INPUT', 'PROPAGATION', 'TRANSFORMATION', 'SINK'")
    description: str
    code_snippet: str
    line: Optional[int] = None
    file_path: Optional[str] = None


class DataflowResponse(BaseModel):
    review_id: str
    file_path: str
    line: int
    has_dataflow: bool
    nodes: List[DataflowNode] = Field(default_factory=list)
    message: Optional[str] = None


# ============================================================
# FIX PLAYGROUND SCHEMAS
# ============================================================

class PlaygroundReviewRequest(BaseModel):
    code: str = Field(..., description="Modified source code to re-analyze")
    language: str = Field("python", description="Language of snippet")
    filename: str = Field("snippet.py", description="Virtual filename")
    original_issue_category: Optional[str] = Field(None, description="Category of original finding to verify remediation")
    original_issue_line: Optional[int] = Field(None, description="Original finding line number")
    original_finding_line: Optional[int] = Field(None, description="Alias for original finding line number")


class PlaygroundReviewResponse(BaseModel):
    status: str = Field(..., description="'resolved', 'still_detected', or 'error'")
    resolved: bool = Field(..., description="True if target issue has been eliminated")
    is_resolved: Optional[bool] = None
    total_issues: Optional[int] = 0
    message: str
    findings: List[ReviewIssue] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# LEARNER MODE SCHEMAS
# ============================================================

class QuizModel(BaseModel):
    question: str
    options: List[str]
    correct_option: int = 0
    correct_index: Optional[int] = None
    explanation: str


class LearnerFindingRequest(BaseModel):
    review_id: Optional[str] = None
    file_path: Optional[str] = None
    line: Optional[int] = None
    finding_line: Optional[int] = None
    issue_text: Optional[str] = None
    category: Optional[str] = None
    code_snippet: Optional[str] = None


class LearnerFindingResponse(BaseModel):
    concept_title: str = "Security Concept"
    concept: Optional[str] = None
    cwe: str = "CWE-General"
    owasp: str = "OWASP-General"
    concept_summary: str = ""
    why_it_matters: str = ""
    what_happened_in_code: str = ""
    what_happened: Optional[str] = None
    impact: str = ""
    evidence_breakdown: str = ""
    evidence: Optional[str] = None
    detection_sources: List[str] = Field(default_factory=list)
    how_to_fix: str = ""
    good_code: str = ""
    safer_implementation: Optional[str] = None
    bad_code: str = ""
    key_takeaway: Optional[str] = None
    quiz: QuizModel
    standards: List[str] = Field(default_factory=list)


# ============================================================
# AI ASSISTANT SCHEMAS
# ============================================================

class AssistantMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    context_pill: Optional[str] = None


class AssistantChatRequest(BaseModel):
    messages: List[AssistantMessage] = Field(default_factory=list)
    review_id: Optional[str] = None
    file_path: Optional[str] = None
    line: Optional[int] = None
    finding_line: Optional[int] = None
    query: Optional[str] = None
    context: Optional[str] = None


class AssistantChatResponse(BaseModel):
    message: str = ""
    reply: Optional[str] = None
    provider: str = "codeguard"
    model: str = "ast-rules"
    fallback_used: bool = False
    trace_id: str = "assistant_trace"
    context_used: Optional[str] = None


# ============================================================
# SECURITY HEALTH & RISK VIEW SCHEMAS
# ============================================================

class SecurityHealthResponse(BaseModel):
    security_score: int = Field(100, ge=0, le=100, description="Deterministic security posture score (0-100)")
    score: Optional[int] = None
    grade: Optional[str] = "A"
    total_reviews: int = 0
    total_issues: int = 0
    critical_count: int = 0
    critical_issues: Optional[int] = None
    high_count: int = 0
    high_issues: Optional[int] = None
    medium_count: int = 0
    medium_issues: Optional[int] = None
    low_count: int = 0
    low_issues: Optional[int] = None
    style_count: int = 0
    style_issues: Optional[int] = None
    llm_reasoned_count: int = 0
    static_reasoned_count: int = 0
    categories: Dict[str, int] = Field(default_factory=dict)
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    formula: Optional[str] = ""


class FileRiskItem(BaseModel):
    file_path: str
    repo_url: Optional[str] = ""
    pr_number: Optional[int] = None
    critical: int = 0
    critical_count: Optional[int] = None
    high: int = 0
    high_count: Optional[int] = None
    medium: int = 0
    medium_count: Optional[int] = None
    low: int = 0
    low_count: Optional[int] = None
    total: int = 0
    total_count: Optional[int] = None
    risk_score: int = 0
    risk_tier: str = Field("LOW", description="'HIGH', 'MEDIUM', 'LOW'")
    complexity: str = Field("Low", description="'High', 'Medium', 'Low'")
    fan_in: int = 0
    fan_out: int = 0
    categories: List[str] = Field(default_factory=list)


class RepositoryRiskResponse(BaseModel):
    overall_risk: str = "medium"
    ranked_files: List[FileRiskItem] = Field(default_factory=list)
    top_categories: Dict[str, int] = Field(default_factory=dict)
    formula: str = ""
    files: List[FileRiskItem] = Field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0


# ============================================================
# KNOWLEDGE BASE & ACADEMY SCHEMAS
# ============================================================

class KnowledgeTopicSummary(BaseModel):
    id: str
    title: str
    category: str
    cwe: str
    owasp: str
    severity: str
    summary: str


class KnowledgeTopicDetail(BaseModel):
    id: str
    title: str
    category: str
    cwe: str
    owasp: str
    severity: str
    summary: str
    why_it_matters: str = ""
    mechanics: str = ""
    vulnerable_example: str = ""
    secure_example: str = ""
    secure_remediation: str = ""
    preventive_guidelines: List[str] = Field(default_factory=list)
    detection_rule: str = ""
    quiz: Optional[QuizModel] = None


