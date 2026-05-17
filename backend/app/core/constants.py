"""
CodeGuard — Constants and enumerations.

Central definition of severity levels, confidence thresholds,
issue types, and supported languages used across all pipeline stages.
"""

from __future__ import annotations

from enum import Enum


# ── Severity Levels ──────────────────────────────────────────────
class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ── Issue Source ─────────────────────────────────────────────────
class IssueSource(str, Enum):
    STATIC_ANALYSIS = "static_analysis"
    LINTER = "linter"
    LLM = "llm"
    COMBINED = "combined"


# ── Issue Types ──────────────────────────────────────────────────
class IssueType(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_SMELL = "code_smell"
    STYLE = "style"
    COMPLEXITY = "complexity"
    DEAD_CODE = "dead_code"
    TYPE_ERROR = "type_error"
    CONCURRENCY = "concurrency"
    ERROR_HANDLING = "error_handling"
    BEST_PRACTICE = "best_practice"


# ── Pipeline Stages ─────────────────────────────────────────────
class PipelineStage(str, Enum):
    INPUT_VALIDATION = "input_validation"
    REPO_CLONE = "repo_clone"
    DIFF_EXTRACTION = "diff_extraction"
    DIFF_PARSING = "diff_parsing"
    STATIC_ANALYSIS = "static_analysis"
    LINTER_ANALYSIS = "linter_analysis"
    FEATURE_AGGREGATION = "feature_aggregation"
    LLM_REASONING = "llm_reasoning"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    FIX_SUGGESTION = "fix_suggestion"
    REVIEW_ASSEMBLY = "review_assembly"
    EVALUATION = "evaluation"
    STORAGE = "storage"


# ── Pipeline Status ──────────────────────────────────────────────
class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ── Supported Languages ─────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
}

# ── Confidence Thresholds ────────────────────────────────────────
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# ── Complexity Thresholds ────────────────────────────────────────
COMPLEXITY_THRESHOLDS = {
    "low": 5,
    "moderate": 10,
    "high": 20,
    "very_high": 40,
}

# ── Dangerous Patterns ──────────────────────────────────────────
DANGEROUS_BUILTINS = {"eval", "exec", "compile", "__import__"}
MUTABLE_DEFAULT_TYPES = {"list", "dict", "set", "List", "Dict", "Set"}
