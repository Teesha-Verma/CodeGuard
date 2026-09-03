"""
CodeGuard V2 — Normalized LLM Models and Data Structures.

Provides provider-agnostic request, response, and health structures.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProviderHealthState(str, Enum):
    """Health / availability states for LLM providers."""
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    UNAVAILABLE = "UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class LLMRequest(BaseModel):
    """Normalized provider-neutral request structure."""
    system_prompt: str = Field("", description="System instruction prompt")
    user_prompt: str = Field(..., description="User prompt or payload")
    temperature: float = Field(0.2, description="Sampling temperature")
    max_tokens: int = Field(4096, description="Maximum completion tokens")
    response_format: str = Field("json", description="Expected format: 'json' or 'text'")
    timeout: float = Field(60.0, description="Per-request timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary trace/request context")


class LLMResponse(BaseModel):
    """Normalized provider-neutral response structure."""
    model_config = {"arbitrary_types_allowed": True}

    text: str = Field("", description="Raw output text from model")
    parsed_json: Optional[Dict[str, Any]] = Field(None, description="Parsed structured JSON if requested")
    provider: str = Field(..., description="Provider name that generated the response ('groq' | 'gemini')")
    model: str = Field(..., description="Specific model that generated the response")
    input_tokens: int = Field(0, description="Prompt / input tokens consumed")
    output_tokens: int = Field(0, description="Completion / candidate tokens consumed")
    total_tokens: int = Field(0, description="Total tokens consumed")
    latency_ms: float = Field(0.0, description="Request execution latency in milliseconds")
    finish_reason: Optional[Any] = Field(None, description="Model finish reason if available")
    fallback_used: bool = Field(False, description="True if response was produced by a fallback provider")
    error: Optional[str] = Field(None, description="Error message if failed")
    request_id: Optional[Any] = Field(None, description="Trace or provider request ID")

    @property
    def is_success(self) -> bool:
        """True if the response completed successfully with content and no error."""
        return (bool(self.text) or self.parsed_json is not None) and not self.error
