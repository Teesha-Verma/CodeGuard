"""
CodeGuard V2 — Google Gemini LLM Provider.

Handles LLM reasoning via the official Google GenAI Python SDK (google-genai)
with JSON structured output, rate-limit awareness, and zero-retry quota failover.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import get_settings
from app.llm.errors import ErrorCategory, ErrorClassification
from app.llm.models import LLMRequest, LLMResponse
from app.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider using the modern Google GenAI SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        api_url: Optional[str] = None,
    ):
        settings = get_settings()
        self._api_key = (
            api_key
            or getattr(settings, "GEMINI_API_KEY", "")
            or getattr(settings, "LLM_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
        )
        self._primary_model = (
            primary_model
            or getattr(settings, "GEMINI_LLM_MODEL", None)
            or getattr(settings, "GEMINI_PRIMARY_MODEL", None)
            or "gemini-2.5-flash"
        )
        self._fallback_models = (
            fallback_models
            if fallback_models is not None
            else getattr(
                settings,
                "gemini_fallback_model_list",
                ["gemini-2.5-flash-lite"]
            )
        )
        self._timeout = timeout or getattr(settings, "GEMINI_TIMEOUT", 60.0)
        self._max_retries = (
            max_retries
            if max_retries is not None
            else max(1, getattr(settings, "GEMINI_MAX_RETRIES", 2))
        )
        self._api_url = api_url or getattr(settings, "GEMINI_API_BASE_URL", None)
        self._backoff_base = getattr(settings, "LLM_BACKOFF_BASE_SECONDS", 1.5)
        self._client = None

        if self.is_available():
            try:
                http_options = None
                if self._api_url and "googleapis.com" not in self._api_url and types:
                    http_options = types.HttpOptions(base_url=self._api_url)
                self._client = genai.Client(api_key=self._api_key, http_options=http_options)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client for LLM: {e}")

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def primary_model(self) -> str:
        return self._primary_model

    @property
    def fallback_models(self) -> List[str]:
        return list(self._fallback_models)

    def is_available(self) -> bool:
        """Check if google-genai library is installed and key is configured."""
        if genai is None:
            return False
        effective_key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
        return bool(effective_key and effective_key not in ("mock_key", "your_gemini_api_key_here"))

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai is not installed. Please install it with 'pip install google-genai'.")
            effective_key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_gemini_api_key_here"):
                raise ValueError("Gemini API key is required when Gemini provider is enabled.")
            self._client = genai.Client(api_key=effective_key)
        return self._client

    def generate(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate unstructured text response from Gemini."""
        return self._execute(request, tracker=tracker, structured=False)

    def generate_structured(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate structured JSON response from Gemini."""
        return self._execute(request, tracker=tracker, structured=True)

    def _execute(self, request: LLMRequest, tracker: Optional[Any] = None, structured: bool = True) -> LLMResponse:
        """Execute request across candidate models with classification and bounded retry."""
        if not self.is_available():
            return LLMResponse(
                text="",
                provider=self.name,
                model=self.primary_model,
                error="Gemini API key is not configured."
            )

        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        if tracker is not None and hasattr(tracker, "get_available_models"):
            candidate_models = tracker.get_available_models(self.primary_model, self.fallback_models)

        if not candidate_models:
            return LLMResponse(
                text="",
                provider=self.name,
                model=self.primary_model,
                error="All Gemini models are exhausted for this review."
            )

        gen_config = None
        if types is not None:
            config_kwargs: Dict[str, Any] = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
            }
            if request.system_prompt:
                config_kwargs["system_instruction"] = request.system_prompt
            if structured:
                config_kwargs["response_mime_type"] = "application/json"
            if hasattr(types, "AutomaticFunctionCallingConfig"):
                config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
            gen_config = types.GenerateContentConfig(**config_kwargs)

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
                    response = client.models.generate_content(
                        model=current_model,
                        contents=request.user_prompt,
                        config=gen_config,
                    )
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    content = response.text if hasattr(response, "text") else str(response)
                    parsed = None
                    if structured:
                        parsed = self.parse_json_safely(content)
                        if parsed is None and content:
                            if attempt < self._max_retries:
                                logger.warning(f"Gemini ({current_model}) returned invalid JSON; retrying attempt {attempt}.")
                                continue
                            else:
                                if tracker is not None and hasattr(tracker, "record_failure"):
                                    tracker.record_failure(current_model, "json_parse_error")
                                break

                    # Token accounting
                    prompt_tokens = 0
                    completion_tokens = 0
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                        completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

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
                    )

                except Exception as e:
                    last_error = e
                    classification = self.classify_error(e)
                    logger.debug(f"Gemini API error on model {current_model} (attempt {attempt}): {classification.category.value} - {e}")

                    if tracker is not None and hasattr(tracker, "record_failure"):
                        tracker.record_failure(current_model, f"{classification.category.value}: {e}")
                    if tracker is not None and hasattr(tracker, "record_provider_failure"):
                        tracker.record_provider_failure(self.name, current_model, classification.category.value, str(e))

                    # 1. Model Not Found -> skip to next fallback model immediately
                    if classification.category == ErrorCategory.MODEL_NOT_FOUND:
                        if tracker is not None and hasattr(tracker, "mark_model_exhausted"):
                            tracker.mark_model_exhausted(current_model, "model_not_found")
                        logger.warning(f"Gemini model {current_model} not available; switching to fallback model.")
                        break

                    # 2. Daily Quota Exhaustion -> ZERO RETRIES on this model, switch immediately to fallback model
                    if classification.is_quota_exhaustion:
                        if tracker is not None and hasattr(tracker, "mark_model_exhausted"):
                            tracker.mark_model_exhausted(current_model, "daily_quota_exhausted")
                        logger.warning(
                            f"Gemini model {current_model} exhausted daily quota; skipping remaining retries and trying fallback model."
                        )
                        break

                    # 3. Auth Error -> Fatal configuration issue, no retries
                    if classification.category == ErrorCategory.AUTH_ERROR:
                        logger.error(f"Gemini authentication error: {e}")
                        return LLMResponse(
                            text="",
                            provider=self.name,
                            model=current_model,
                            error=f"AUTH_ERROR: {e}"
                        )

                    # 4. Temporary RPM Rate Limit -> Bounded retry with backoff
                    if classification.category == ErrorCategory.TEMPORARY_RATE_LIMIT:
                        if attempt < self._max_retries:
                            sleep_time = classification.retry_after or min(
                                3.0, self._backoff_base * (1.5 ** attempt) + random.uniform(0.1, 0.3)
                            )
                            logger.info(f"Temporary Gemini rate limit for {current_model}; retrying in {sleep_time:.1f}s.")
                            time.sleep(sleep_time)
                            continue
                        else:
                            if tracker is not None and hasattr(tracker, "mark_model_rate_limited"):
                                tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            logger.warning(f"Gemini rate limit exceeded max retries on {current_model}; switching to next fallback.")
                            break

                    # 5. Server Error (500 / 503) or Timeout -> Bounded retry
                    if classification.category in (ErrorCategory.SERVER_ERROR, ErrorCategory.TIMEOUT):
                        if attempt < self._max_retries:
                            sleep_time = self._backoff_base * attempt
                            time.sleep(sleep_time)
                            continue
                        else:
                            break

                    # Other non-retryable error
                    break

        if tracker is not None and hasattr(tracker, "mark_provider_exhausted"):
            tracker.mark_provider_exhausted(self.name, "all_models_failed_or_exhausted")

        return LLMResponse(
            text="",
            provider=self.name,
            model=last_model,
            error=f"All Gemini models failed. Last error: {last_error}"
        )
