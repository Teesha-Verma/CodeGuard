"""
CodeGuard V2 — Review LLM Request Budget & Quota Tracker.

Manages per-review request budgets, exhausted model tracking, rate-limit cooldowns,
and degraded mode signaling to prevent retry storms and runaway API calls.
"""
from __future__ import annotations

import time
import threading
import logging
from typing import Dict, List, Optional, Set

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ReviewLLMTracker:
    """
    Thread-safe tracker managing the LLM request budget and quota availability for a single review.
    """

    def __init__(self, review_id: str, max_requests: Optional[int] = None):
        self.review_id = review_id or "default"
        settings = get_settings()
        self.max_requests = max_requests if max_requests is not None else settings.LLM_MAX_GENERATION_REQUESTS_PER_REVIEW
        self.requests_made = 0
        self.exhausted_models: Set[str] = set()
        self.temporarily_limited_models: Dict[str, float] = {}  # model -> cooldown_until_timestamp
        self.degraded_mode = False
        self.degraded_reason: Optional[str] = None
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

    def set_degraded_mode(self, reason: str) -> None:
        """Mark the review as operating in degraded mode (deterministic analysis only)."""
        with self._lock:
            self.degraded_mode = True
            self.degraded_reason = reason
            logger.warning(f"Review {self.review_id}: Set degraded mode due to '{reason}'.")

    def get_status(self) -> Dict[str, Any]:
        """Return snapshot of tracker status."""
        with self._lock:
            return {
                "review_id": self.review_id,
                "requests_made": self.requests_made,
                "max_requests": self.max_requests,
                "remaining_budget": max(0, self.max_requests - self.requests_made),
                "exhausted_models": list(self.exhausted_models),
                "degraded_mode": self.degraded_mode,
                "degraded_reason": self.degraded_reason,
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
