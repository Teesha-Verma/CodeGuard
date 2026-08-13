"""
Structured response schemas for the LLM output.
"""
from typing import Any
from pydantic import BaseModel, Field


class ReviewFinding(BaseModel):
    """Represents a single finding from the code review."""
    title: str = Field(description="Short title for the finding.")
    severity: str = Field(description="Severity of the finding (e.g., low, medium, high, critical).")
    file_path: str = Field(description="Path to the file where the finding was identified.")
    line_number: int | None = Field(default=None, description="Line number of the finding, if applicable.")
    evidence: str = Field(description="Code snippet or context acting as evidence.")
    reasoning: str = Field(description="Detailed reasoning for why this is a finding.")
    priority: str = Field(default="medium", description="Priority for fixing the finding.")
    remediation: str = Field(description="Steps or suggestions to fix the issue.")
    code_suggestion: str = Field(default="", description="Proposed code changes.")
    references: list[str] = Field(default_factory=list, description="References to CWE, documentation, etc.")


class ReviewResponse(BaseModel):
    """The structured review object returned by the LLM."""
    review_summary: str = Field(description="Overall summary of the review.")
    overall_severity: str = Field(description="Overall severity of the codebase.")
    findings: list[ReviewFinding] = Field(description="List of identified findings.")
    evidence_summary: str = Field(description="Summary of the evidence gathered.")
    reasoning_trace: str = Field(description="High-level reasoning trace of the review.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    priority: str = Field(description="Overall priority for addressing findings.")
    remediation_summary: str = Field(description="Summary of remediation steps.")
    code_suggestions: list[str] = Field(default_factory=list, description="Overall code suggestions.")
    references: list[str] = Field(default_factory=list, description="Global references.")
    review_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata related to the review.")

TypedReviewObject = ReviewResponse
