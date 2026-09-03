"""
CodeGuard V2 — LLM Error Classification and Fault Tolerance.

Categorizes provider exceptions into actionable classes:
- TEMPORARY_RATE_LIMIT -> bounded retry with exponential backoff
- QUOTA_EXHAUSTED -> ZERO retries, immediate failover to fallback provider
- AUTH_ERROR -> fail fast, report configuration problem
- SERVER_ERROR -> bounded retry
- BAD_REQUEST -> non-retryable
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Categorized failure types for LLM provider errors."""
    TEMPORARY_RATE_LIMIT = "TEMPORARY_RATE_LIMIT"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    AUTH_ERROR = "AUTH_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    CONTENT_FILTER = "CONTENT_FILTER"
    UNKNOWN = "UNKNOWN"


class ErrorClassification(BaseModel):
    """Normalized assessment of an LLM exception."""
    category: ErrorCategory
    is_retryable: bool = False
    is_quota_exhausted: bool = False
    retry_after: Optional[float] = None
    message: str = ""

    @property
    def is_quota_exhaustion(self) -> bool:
        return self.is_quota_exhausted or self.category == ErrorCategory.QUOTA_EXHAUSTED


class ErrorClassifier:
    """Classifies provider-specific exceptions into unified ErrorClassification."""

    DAILY_QUOTA_TERMS = [
        "tpd", "tokens per day", "tokens_per_day", "tpd limit",
        "rpd", "requests per day", "requests_per_day",
        "generaterequestsperday", "dayperproject", "per_day", "perday",
        "daily token quota", "tokens per day limit", "daily quota",
        "quota_exceeded", "daily", "free_tier_requests_per_day"
    ]

    TEMPORARY_RPM_TERMS = [
        "rate_limit_exceeded", "requests per minute", "tokens per minute",
        "generaterequestsperminute", "minuteperproject", "perminute",
        "tpm", "rpm", "too many requests", "resource_exhausted"
    ]

    AUTH_TERMS = [
        "invalid_api_key", "unauthorized", "permission_denied",
        "api key not valid", "forbidden", "authentication",
        "bad api key", "invalid api key"
    ]

    MODEL_NOT_FOUND_TERMS = [
        "model_not_found", "does not exist", "do not have access",
        "terms acceptance", "terms_required", "unknown model",
        "is not found for api version"
    ]

    @classmethod
    def classify(cls, error: Exception, provider: str = "") -> ErrorClassification:
        """Classify any exception into an ErrorClassification."""
        err_str = str(error).lower()
        err_repr = repr(error).lower()
        combined_text = f"{err_str} {err_repr}"

        # 1. Inspect status codes if available
        status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
        if status_code is None:
            # Check for HTTP status in text using word boundaries to avoid false matches (e.g. 198401 tokens)
            if re.search(r"\b429\b", combined_text) or "too many requests" in combined_text or "rate limit" in combined_text:
                status_code = 429
            elif re.search(r"\b(401|403)\b", combined_text):
                status_code = 401
            elif re.search(r"\b(500|502|503|504)\b", combined_text):
                status_code = 503
            elif re.search(r"\b(400|422)\b", combined_text):
                status_code = 400

        # Extract retry_after header or hint if present
        retry_after: Optional[float] = None
        headers = getattr(error, "headers", None)
        if isinstance(headers, dict) and "retry-after" in headers:
            try:
                retry_after = float(headers["retry-after"])
            except (ValueError, TypeError):
                pass

        if retry_after is None:
            # Search for "retry after X seconds" or "in Xs"
            match = re.search(r"retry after ([\d\.]+)\s*(?:seconds|s)", combined_text)
            if match:
                try:
                    retry_after = float(match.group(1))
                except (ValueError, TypeError):
                    pass

        # 2. Check Daily Quota Exhaustion (MUST take precedence over transient 429 and status codes)
        if any(t in combined_text for t in cls.DAILY_QUOTA_TERMS):
            return ErrorClassification(
                category=ErrorCategory.QUOTA_EXHAUSTED,
                is_retryable=False,
                is_quota_exhausted=True,
                message=str(error)
            )

        # 3. Check Auth Errors
        if (status_code in (401, 403) and not ("rate limit" in combined_text or "tpd" in combined_text)) or any(t in combined_text for t in cls.AUTH_TERMS):
            return ErrorClassification(
                category=ErrorCategory.AUTH_ERROR,
                is_retryable=False,
                is_quota_exhausted=False,
                message=str(error)
            )

        # 4. Check Model Not Found
        if any(t in combined_text for t in cls.MODEL_NOT_FOUND_TERMS):
            return ErrorClassification(
                category=ErrorCategory.MODEL_NOT_FOUND,
                is_retryable=False,
                is_quota_exhausted=False,
                message=str(error)
            )

        # 5. Check Temporary RPM / TPM Rate Limit
        if status_code == 429 or any(t in combined_text for t in cls.TEMPORARY_RPM_TERMS):
            return ErrorClassification(
                category=ErrorCategory.TEMPORARY_RATE_LIMIT,
                is_retryable=True,
                is_quota_exhausted=False,
                retry_after=retry_after,
                message=str(error)
            )

        # 6. Check Timeouts
        if "timed out" in combined_text or "timeout" in combined_text:
            return ErrorClassification(
                category=ErrorCategory.TIMEOUT,
                is_retryable=True,
                is_quota_exhausted=False,
                message=str(error)
            )

        # 7. Check Server Errors (500, 502, 503, 504)
        if status_code in (500, 502, 503, 504):
            return ErrorClassification(
                category=ErrorCategory.SERVER_ERROR,
                is_retryable=True,
                is_quota_exhausted=False,
                message=str(error)
            )

        # 8. Check Bad Request
        if status_code == 400:
            return ErrorClassification(
                category=ErrorCategory.BAD_REQUEST,
                is_retryable=False,
                is_quota_exhausted=False,
                message=str(error)
            )

        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            is_retryable=False,
            is_quota_exhausted=False,
            message=str(error)
        )
