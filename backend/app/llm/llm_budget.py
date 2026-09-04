"""
CodeGuard V2 — Review LLM Request Budget & Quota Tracker.

Manages per-review request budgets, exhausted model tracking, rate-limit cooldowns,
degraded mode signaling, and detailed per-review request accounting to prevent
retry storms and runaway API calls.
"""
from __future__ import annotations

import time
import threading
import logging
from typing import Dict, List, Optional, Set, Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ReviewLLMTracker:
    """
    Thread-safe tracker managing the LLM request budget, quota availability,
    and detailed request accounting for a single review.
    """

    def __init__(self, review_id: str, max_requests: Optional[int] = None):
        self.review_id = review_id or "default"
        settings = get_settings()
        self.max_requests = (
            max_requests
            if max_requests is not None
            else getattr(settings, "LLM_MAX_GENERATION_REQUESTS_PER_REVIEW", 25)
        )
        self.requests_made = 0
        self.exhausted_models: Set[str] = set()
        self.temporarily_limited_models: Dict[str, float] = {}  # model -> cooldown_until_timestamp
        self.degraded_mode = False
        self.degraded_reason: Optional[str] = None

        # Per-review accounting metrics (Problem 17)
        self.llm_requests_attempted: int = 0
        self.llm_requests_succeeded: int = 0
        self.llm_requests_failed: int = 0
        self.llm_requests_skipped_low_signal: int = 0
        self.llm_requests_skipped_budget: int = 0
        self.llm_models_used: Set[str] = set()
        self.llm_tokens_requested: int = 0
        self.llm_tokens_used: int = 0

        # Multi-provider state and metrics
        self.exhausted_providers: Set[str] = set()
        self.provider_metrics: Dict[str, Dict[str, Any]] = {
            "groq": {
                "requests": 0, "successes": 0, "failures": 0,
                "rate_limits": 0, "quota_exhaustions": 0,
                "fallbacks_triggered": 0, "fallback_requests": 0,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "total_latency_ms": 0.0
            },
            "gemini": {
                "requests": 0, "successes": 0, "failures": 0,
                "rate_limits": 0, "quota_exhaustions": 0,
                "fallbacks_triggered": 0, "fallback_requests": 0,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "total_latency_ms": 0.0
            }
        }

        self._lock = threading.Lock()

    def can_request(self) -> bool:
        """Check if review has remaining request budget and is not in hard degraded mode."""
        with self._lock:
            if self.degraded_mode and len(self.exhausted_models) > 0 and self.requests_made >= self.max_requests:
                return False
            return self.requests_made < self.max_requests

    def record_request(self) -> int:
        """Increment and return the number of requests made for this review."""
        with self._lock:
            self.requests_made += 1
            if self.requests_made >= self.max_requests:
                logger.info(f"Review {self.review_id}: LLM request budget reached ({self.requests_made}/{self.max_requests}).")
            return self.requests_made

    def remaining_budget(self) -> int:
        """Return remaining allowed generation requests."""
        with self._lock:
            return max(0, self.max_requests - self.requests_made)

    def record_attempt(self, model: str) -> None:
        """Record an attempt to call an LLM model."""
        with self._lock:
            self.llm_requests_attempted += 1
            if model:
                self.llm_models_used.add(model)

    def record_success(self, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Record a successful LLM reasoning generation and token usage."""
        with self._lock:
            self.llm_requests_succeeded += 1
            if model:
                self.llm_models_used.add(model)
            self.llm_tokens_requested += prompt_tokens
            self.llm_tokens_used += (prompt_tokens + completion_tokens)

    def record_failure(self, model: str, reason: str = "") -> None:
        """Record a failed LLM reasoning call."""
        with self._lock:
            self.llm_requests_failed += 1
            logger.debug(f"Review {self.review_id}: LLM call failed for model '{model}': {reason}")

    def record_skipped_low_signal(self, count: int = 1) -> None:
        """Record findings skipped because they are low-signal/style."""
        with self._lock:
            self.llm_requests_skipped_low_signal += count

    def record_skipped_budget(self, count: int = 1) -> None:
        """Record findings skipped because the review LLM budget was reached."""
        with self._lock:
            self.llm_requests_skipped_budget += count

    def mark_model_exhausted(self, model: str, reason: str = "daily_quota_exhausted") -> None:
        """
        Mark a model as permanently exhausted (e.g. daily quota reached) for this review.
        The model will not be retried for the remainder of this review.
        """
        with self._lock:
            self.exhausted_models.add(model)
            logger.warning(
                f"Review {self.review_id}: Marked model '{model}' as exhausted ({reason}). "
                f"Total exhausted models for this review: {sorted(self.exhausted_models)}"
            )

    def is_model_exhausted(self, model: str) -> bool:
        """Check if model is permanently exhausted for this review."""
        with self._lock:
            return model in self.exhausted_models

    def mark_model_rate_limited(self, model: str, cooldown_seconds: float = 30.0) -> None:
        """Mark a model as temporarily rate-limited with a cooldown expiration."""
        with self._lock:
            self.temporarily_limited_models[model] = time.time() + cooldown_seconds
            logger.info(
                f"Review {self.review_id}: Model '{model}' rate limited. Cooldown for {cooldown_seconds:.1f}s."
            )

    def is_model_rate_limited(self, model: str) -> bool:
        """Check if model is currently under a temporary rate-limit cooldown."""
        with self._lock:
            cooldown_until = self.temporarily_limited_models.get(model, 0.0)
            if cooldown_until > time.time():
                return True
            if model in self.temporarily_limited_models:
                del self.temporarily_limited_models[model]
            return False

    def get_available_models(self, primary_model: str, fallback_models: List[str]) -> List[str]:
        """
        Return an ordered list of candidate models that are neither permanently exhausted
        nor currently under active rate-limit cooldown.
        """
        with self._lock:
            all_candidates = [primary_model] + [m for m in fallback_models if m != primary_model]
            available = []
            now = time.time()
            for m in all_candidates:
                if m in self.exhausted_models:
                    continue
                cooldown_until = self.temporarily_limited_models.get(m, 0.0)
                if cooldown_until > now:
                    continue
                if m not in available:
                    available.append(m)
            return available

    def mark_provider_exhausted(self, provider: str, reason: str = "daily_quota_exhausted") -> None:
        """Mark an entire provider (Groq or Gemini) as exhausted for this review."""
        with self._lock:
            p_key = provider.lower()
            self.exhausted_providers.add(p_key)
            if p_key in self.provider_metrics:
                self.provider_metrics[p_key]["quota_exhaustions"] += 1
            logger.warning(
                f"Review {self.review_id}: Marked provider '{provider}' as exhausted ({reason}). "
                f"Active exhausted providers: {sorted(self.exhausted_providers)}"
            )

    def is_provider_exhausted(self, provider: str) -> bool:
        """Check if provider is exhausted for this review."""
        with self._lock:
            return provider.lower() in self.exhausted_providers

    def record_provider_attempt(self, provider: str, model: str) -> None:
        """Record a provider call attempt."""
        with self._lock:
            p_key = provider.lower()
            if p_key not in self.provider_metrics:
                self.provider_metrics[p_key] = {
                    "requests": 0, "successes": 0, "failures": 0,
                    "rate_limits": 0, "quota_exhaustions": 0,
                    "fallbacks_triggered": 0, "fallback_requests": 0,
                    "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                    "total_latency_ms": 0.0
                }
            self.provider_metrics[p_key]["requests"] += 1
            if model:
                self.llm_models_used.add(model)

    def record_provider_success(
        self,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        fallback_used: bool = False
    ) -> None:
        """Record successful generation from a provider."""
        with self._lock:
            p_key = provider.lower()
            if p_key not in self.provider_metrics:
                self.provider_metrics[p_key] = {
                    "requests": 0, "successes": 0, "failures": 0,
                    "rate_limits": 0, "quota_exhaustions": 0,
                    "fallbacks_triggered": 0, "fallback_requests": 0,
                    "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                    "total_latency_ms": 0.0
                }
            metrics = self.provider_metrics[p_key]
            metrics["successes"] += 1
            metrics["prompt_tokens"] += prompt_tokens
            metrics["completion_tokens"] += completion_tokens
            metrics["total_tokens"] += (prompt_tokens + completion_tokens)
            metrics["total_latency_ms"] += latency_ms
            if fallback_used:
                metrics["fallback_requests"] += 1

    def record_provider_failure(self, provider: str, model: str, error_category: str, reason: str = "") -> None:
        """Record failed generation from a provider."""
        with self._lock:
            p_key = provider.lower()
            if p_key not in self.provider_metrics:
                self.provider_metrics[p_key] = {
                    "requests": 0, "successes": 0, "failures": 0,
                    "rate_limits": 0, "quota_exhaustions": 0,
                    "fallbacks_triggered": 0, "fallback_requests": 0,
                    "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                    "total_latency_ms": 0.0
                }
            metrics = self.provider_metrics[p_key]
            metrics["failures"] += 1
            if error_category == "TEMPORARY_RATE_LIMIT":
                metrics["rate_limits"] += 1
            elif error_category == "QUOTA_EXHAUSTED":
                metrics["quota_exhaustions"] += 1

    def record_provider_fallback(self, from_provider: str, to_provider: str) -> None:
        """Record that a fallback occurred between providers."""
        with self._lock:
            from_key = from_provider.lower()
            to_key = to_provider.lower()
            if from_key in self.provider_metrics:
                self.provider_metrics[from_key]["fallbacks_triggered"] += 1
            if to_key in self.provider_metrics:
                self.provider_metrics[to_key]["fallback_requests"] += 1

    def set_degraded_mode(self, reason: str) -> None:
        """Mark the review as operating in degraded mode (deterministic analysis only)."""
        with self._lock:
            self.degraded_mode = True
            self.degraded_reason = reason
            logger.warning(f"Review {self.review_id}: Set degraded mode due to '{reason}'.")

    def get_status(self) -> Dict[str, Any]:
        """Return snapshot of tracker status including full accounting."""
        with self._lock:
            return {
                "review_id": self.review_id,
                "requests_made": self.requests_made,
                "max_requests": self.max_requests,
                "remaining_budget": max(0, self.max_requests - self.requests_made),
                "exhausted_models": list(self.exhausted_models),
                "exhausted_providers": list(self.exhausted_providers),
                "degraded_mode": self.degraded_mode,
                "degraded_reason": self.degraded_reason,
                # Accounting metrics
                "llm_requests_attempted": self.llm_requests_attempted,
                "llm_requests_succeeded": self.llm_requests_succeeded,
                "llm_requests_failed": self.llm_requests_failed,
                "llm_requests_skipped_low_signal": self.llm_requests_skipped_low_signal,
                "llm_requests_skipped_budget": self.llm_requests_skipped_budget,
                "llm_models_used": sorted(self.llm_models_used),
                "llm_tokens_requested": self.llm_tokens_requested,
                "llm_tokens_used": self.llm_tokens_used,
                "provider_metrics": {k: dict(v) for k, v in self.provider_metrics.items()},
            }


# ── Global Registry ──────────────────────────────────────────────
_registry_lock = threading.Lock()
_review_trackers: Dict[str, ReviewLLMTracker] = {}


def get_review_tracker(review_id: str, max_requests: Optional[int] = None) -> ReviewLLMTracker:
    """Get or create the ReviewLLMTracker singleton for the given review_id."""
    key = review_id or "default"
    with _registry_lock:
        if key not in _review_trackers:
            _review_trackers[key] = ReviewLLMTracker(review_id=key, max_requests=max_requests)
        return _review_trackers[key]


def reset_review_tracker(review_id: Optional[str] = None) -> None:
    """Reset tracker for a specific review or all reviews (useful in tests)."""
    with _registry_lock:
        if review_id:
            if review_id in _review_trackers:
                del _review_trackers[review_id]
        else:
            _review_trackers.clear()
