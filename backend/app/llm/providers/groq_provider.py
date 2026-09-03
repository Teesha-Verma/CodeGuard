"""
CodeGuard V2 — Groq LLM Provider.

Handles LLM reasoning via Groq API with multi-model fallback,
zero-retry daily quota exhaustion, and structured JSON output.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional

try:
    import groq
    from groq import Groq
except ImportError:
    groq = None
    Groq = None

from app.core.config import get_settings
from app.llm.errors import ErrorCategory, ErrorClassification
from app.llm.models import LLMRequest, LLMResponse
from app.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq LLM Provider for high-throughput code review reasoning."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        settings = get_settings()
        self._api_key = (
            api_key
            or getattr(settings, "GROQ_API_KEY", "")
            or getattr(settings, "LLM_API_KEY", "")
            or os.environ.get("GROQ_API_KEY", "")
        )
        self._primary_model = (
            primary_model
            or getattr(settings, "GROQ_PRIMARY_MODEL", None)
            or getattr(settings, "GROQ_LLM_MODEL", None)
            or getattr(settings, "LLM_MODEL", None)
            or "llama-3.3-70b-versatile"
        )
        self._fallback_models = (
            fallback_models
            if fallback_models is not None
            else getattr(
                settings,
                "groq_fallback_model_list",
                ["qwen/qwen3.8-27b", "groq/compound-mini", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            )
        )
        self._timeout = timeout or getattr(settings, "GROQ_TIMEOUT", 60.0)
        self._max_retries = (
            max_retries
            if max_retries is not None
            else max(1, getattr(settings, "GROQ_MAX_RETRIES", 2))
        )
        self._backoff_base = getattr(settings, "LLM_BACKOFF_BASE_SECONDS", 1.5)
        self._client: Optional[Groq] = None

        if self.is_available():
            try:
                self._client = Groq(api_key=self._api_key, timeout=self._timeout)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    @property
    def name(self) -> str:
        return "groq"

    @property
    def primary_model(self) -> str:
        return self._primary_model

    @property
    def fallback_models(self) -> List[str]:
        return list(self._fallback_models)

    def is_available(self) -> bool:
        """Check if Groq library is available and key is configured."""
        if Groq is None:
            return False
        effective_key = self._api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY")
        return bool(effective_key and effective_key not in ("mock_key", "your_groq_api_key_here"))

    def _get_client(self) -> Groq:
        if self._client is None:
            if Groq is None:
                raise ImportError("groq is not installed. Please install it with 'pip install groq'.")
            effective_key = self._api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_groq_api_key_here"):
                raise ValueError("Groq API key is required when Groq provider is enabled.")
            self._client = Groq(api_key=effective_key, timeout=self._timeout)
        return self._client

    def generate(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate unstructured text response from Groq."""
        return self._execute(request, tracker=tracker, structured=False)

    def generate_structured(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate structured JSON response from Groq."""
        return self._execute(request, tracker=tracker, structured=True)

    def _execute(self, request: LLMRequest, tracker: Optional[Any] = None, structured: bool = True) -> LLMResponse:
        """Execute request across candidate models with classification and bounded retry."""
        if not self.is_available():
            return LLMResponse(
                text="",
                provider=self.name,
                model=self.primary_model,
                error="Groq API key is not configured."
            )

        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        if tracker is not None and hasattr(tracker, "get_available_models"):
            candidate_models = tracker.get_available_models(self.primary_model, self.fallback_models)

        if not candidate_models:
            return LLMResponse(
                text="",
                provider=self.name,
                model=self.primary_model,
                error="All Groq models are exhausted for this review."
            )

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_prompt})

        last_error = None
        last_model = self.primary_model

        for current_model in candidate_models:
            last_model = current_model
            if tracker is not None and hasattr(tracker, "is_model_exhausted") and tracker.is_model_exhausted(current_model):
                continue

            for attempt in range(1, self._max_retries + 1):
                start_time = time.perf_counter()
                if tracker is not None:
                    if hasattr(tracker, "record_attempt"):
                        tracker.record_attempt(current_model)
                    if hasattr(tracker, "record_provider_attempt"):
                        tracker.record_provider_attempt(self.name, current_model)

                try:
                    client = self._get_client()
                    kwargs: Dict[str, Any] = {
                        "messages": messages,
                        "model": current_model,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                    }
                    if structured:
                        kwargs["response_format"] = {"type": "json_object"}

                    chat_completion = client.chat.completions.create(**kwargs)
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    content = ""
                    finish_reason = None
                    if chat_completion.choices and len(chat_completion.choices) > 0:
                        content = chat_completion.choices[0].message.content or ""
                        raw_fr = getattr(chat_completion.choices[0], "finish_reason", None)
                        if raw_fr is not None and not isinstance(raw_fr, str):
                            finish_reason = str(raw_fr)
                        else:
                            finish_reason = raw_fr

                    raw_id = getattr(chat_completion, "id", None)
                    req_id = str(raw_id) if raw_id is not None and not isinstance(raw_id, str) else raw_id

                    parsed = None
                    if structured:
                        parsed = self.parse_json_safely(content)
                        if parsed is None and content:
                            # Bad JSON returned
                            if attempt < self._max_retries:
                                logger.warning(f"Groq ({current_model}) returned invalid JSON; retrying attempt {attempt}.")
                                continue
                            else:
                                if tracker is not None and hasattr(tracker, "record_failure"):
                                    tracker.record_failure(current_model, "json_parse_error")
                                break

                    # Token accounting
                    prompt_tokens = 0
                    completion_tokens = 0
                    if hasattr(chat_completion, "usage") and chat_completion.usage:
                        prompt_tokens = getattr(chat_completion.usage, "prompt_tokens", 0) or 0
                        completion_tokens = getattr(chat_completion.usage, "completion_tokens", 0) or 0

                    total_tokens = prompt_tokens + completion_tokens

                    if tracker is not None:
                        if hasattr(tracker, "record_success"):
                            tracker.record_success(current_model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
                        if hasattr(tracker, "record_provider_success"):
                            tracker.record_provider_success(
                                provider=self.name,
                                model=current_model,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                latency_ms=latency_ms
                            )

                    return LLMResponse(
                        text=content,
                        parsed_json=parsed,
                        provider=self.name,
                        model=current_model,
                        input_tokens=prompt_tokens,
                        output_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        latency_ms=latency_ms,
                        finish_reason=finish_reason,
                        request_id=req_id
                    )

                except Exception as e:
                    last_error = e
                    classification = self.classify_error(e)
                    logger.debug(f"Groq API error on model {current_model} (attempt {attempt}): {classification.category.value} - {e}")

                    if tracker is not None and hasattr(tracker, "record_failure"):
                        tracker.record_failure(current_model, f"{classification.category.value}: {e}")
                    if tracker is not None and hasattr(tracker, "record_provider_failure"):
                        tracker.record_provider_failure(self.name, current_model, classification.category.value, str(e))

                    # 1. Model Not Found -> skip to next fallback model immediately
                    if classification.category == ErrorCategory.MODEL_NOT_FOUND:
                        if tracker is not None and hasattr(tracker, "mark_model_exhausted"):
                            tracker.mark_model_exhausted(current_model, "model_not_found")
                        logger.warning(f"Groq model {current_model} not available; switching to fallback model.")
                        break

                    # 2. Daily Quota / TPD Exhaustion -> ZERO RETRIES on this model, switch immediately to fallback model
                    if classification.is_quota_exhaustion:
                        if tracker is not None and hasattr(tracker, "mark_model_exhausted"):
                            tracker.mark_model_exhausted(current_model, "daily_token_quota_exhausted")
                        logger.warning(
                            f"Groq model {current_model} exhausted daily token quota; skipping remaining retries and trying fallback model."
                        )
                        break

                    # 3. Auth Error -> Fatal configuration issue, no retries
                    if classification.category == ErrorCategory.AUTH_ERROR:
                        logger.error(f"Groq authentication error: {e}")
                        return LLMResponse(
                            text="",
                            provider=self.name,
                            model=current_model,
                            error=f"AUTH_ERROR: {e}"
                        )

                    # 4. Temporary RPM/TPM Rate Limit -> Bounded retry with backoff
                    if classification.category == ErrorCategory.TEMPORARY_RATE_LIMIT:
                        if attempt < self._max_retries:
                            sleep_time = classification.retry_after or min(
                                3.0, self._backoff_base * (1.5 ** attempt) + random.uniform(0.1, 0.3)
                            )
                            logger.info(f"Temporary Groq rate limit for {current_model}; retrying in {sleep_time:.1f}s.")
                            time.sleep(sleep_time)
                            continue
                        else:
                            if tracker is not None and hasattr(tracker, "mark_model_rate_limited"):
                                tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            logger.warning(f"Groq rate limit exceeded max retries on {current_model}; switching to next fallback.")
                            break

                    # 5. Server Error (500 / 503) or Timeout -> Bounded retry
                    if classification.category in (ErrorCategory.SERVER_ERROR, ErrorCategory.TIMEOUT):
                        if attempt < self._max_retries:
                            sleep_time = self._backoff_base * attempt
                            time.sleep(sleep_time)
                            continue
                        else:
                            break

        if tracker is not None and hasattr(tracker, "mark_provider_exhausted"):
            tracker.mark_provider_exhausted(self.name, "all_models_failed_or_exhausted")

        return LLMResponse(
            text="",
            provider=self.name,
            model=last_model,
            error=f"All Groq models failed. Last error: {last_error}"
        )
