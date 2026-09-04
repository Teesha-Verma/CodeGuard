import re
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMUsageMetrics(BaseModel):
    """Metrics for a single LLM request."""
    provider: str = Field(default="groq", description="The LLM provider (e.g., groq).")
    model_name: str = Field(default="llama-3.3-70b-versatile", description="The name of the LLM model used.")
    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt.")
    completion_tokens: int = Field(default=0, description="Number of tokens in the generated completion.")
    total_tokens: int = Field(default=0, description="Total tokens used (prompt + completion).")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated cost of the request in USD.")
    latency_ms: float = Field(default=0.0, description="Latency of the request in milliseconds.")
    duration_ms: float = Field(default=0.0, description="Total duration of the request in milliseconds.")
    request_size_bytes: int = Field(default=0, description="Size of the request payload in bytes.")
    response_size_bytes: int = Field(default=0, description="Size of the response payload in bytes.")
    success: bool = Field(default=True, description="Whether the request was successful.")
    retry_count: int = Field(default=0, description="Number of retries attempted before success/failure.")
    review_id: Optional[str] = Field(default=None, description="Associated review identifier.")
    trace_id: Optional[str] = Field(default=None, description="Associated trace identifier.")

    def model_post_init(self, __context: Any) -> None:
        if self.duration_ms == 0.0 and self.latency_ms > 0.0:
            self.duration_ms = self.latency_ms
        elif self.latency_ms == 0.0 and self.duration_ms > 0.0:
            self.latency_ms = self.duration_ms
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class LLMTelemetryManager:
    """Manages telemetry and usage metrics for LLM requests."""

    def __init__(self):
        self.history: List[LLMUsageMetrics] = []

    def record_request(self, metrics: LLMUsageMetrics) -> None:
        """
        Records the metrics for an LLM request.

        Args:
            metrics (LLMUsageMetrics): The metrics to record.
        """
        self.history.append(metrics)

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Returns summary statistics for all recorded requests.

        Returns:
            Dict[str, Any]: A dictionary containing total and average metrics.
        """
        total_requests = len(self.history)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
            }

        successful_requests = sum(1 for m in self.history if m.success)
        total_latency = sum(m.latency_ms for m in self.history)

        return {
            "total_requests": total_requests,
            "total_prompt_tokens": sum(m.prompt_tokens for m in self.history),
            "total_completion_tokens": sum(m.completion_tokens for m in self.history),
            "total_tokens": sum(m.total_tokens for m in self.history),
            "total_cost_usd": sum(m.estimated_cost_usd for m in self.history),
            "average_latency_ms": total_latency / total_requests,
            "success_rate": successful_requests / total_requests,
        }

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Redacts API keys, passwords, and sensitive tokens before logging.

        Args:
            prompt (str): The raw prompt string.

        Returns:
            str: The sanitized prompt string.
        """
        # Redact Google Gemini / Google API keys (AIza...)
        redacted = re.sub(
            r"AIza[0-9A-Za-z-_]+",
            "[REDACTED_GEMINI_KEY]",
            prompt,
        )

        # Redact GitHub tokens (ghp_, github_pat_)
        redacted = re.sub(
            r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{40,})",
            "[REDACTED_GITHUB_TOKEN]",
            redacted,
        )

        # Redact database connection strings with passwords
        redacted = re.sub(
            r"postgresql://[^:]+:[^@]+@",
            "postgresql://[REDACTED_USER]:[REDACTED_PASS]@",
            redacted,
        )

        # Redact Bearer tokens
        redacted = re.sub(
            r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{5,}",
            r"\1[REDACTED_TOKEN]",
            redacted,
        )

        # Redact generic api_key / secret key patterns
        redacted = re.sub(
            r"(?i)(api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{5,}['\"]?",
            r"\1=[REDACTED]",
            redacted,
        )

        # Redact any legacy keys if present
        redacted = re.sub(
            r"gsk_[a-zA-Z0-9_\-]+",
            "[REDACTED_KEY]",
            redacted,
        )

        return redacted
