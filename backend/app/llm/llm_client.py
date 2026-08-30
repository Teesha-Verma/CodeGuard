"""
CodeGuard V2 — Grounded Groq LLM Client.

Provider-oriented LLM client supporting Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant)
with JSON structured output, rate-limit awareness, review-level request budgeting,
prompt deduplication/caching, and multi-model fallback cascade.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
import uuid
from typing import Any, Dict, Optional

try:
    import groq
    from groq import Groq
except ImportError:
    groq = None
    Groq = None

from app.core.config import get_settings
from app.core.logger import PipelineLogger
from app.llm.llm_budget import get_review_tracker, ReviewLLMTracker
from app.llm.llm_cache import get_llm_cache, LLMStructuredCache


class LLMClient:
    """Provider-oriented LLM client for generating structured review insights with Groq."""

    def __init__(self, review_id: str = ""):
        self.settings = get_settings()
        self.review_id = review_id or f"session_{uuid.uuid4().hex[:8]}"
        self.logger = PipelineLogger(review_id=self.review_id, stage="llm_client")
        self.provider = getattr(self.settings, "LLM_PROVIDER", "groq")
        self.model = (
            getattr(self.settings, "GROQ_PRIMARY_MODEL", None)
            or getattr(self.settings, "GROQ_LLM_MODEL", None)
            or getattr(self.settings, "LLM_MODEL", None)
            or "llama-3.3-70b-versatile"
        )
        self.api_key = (
            getattr(self.settings, "GROQ_API_KEY", "")
            or getattr(self.settings, "LLM_API_KEY", "")
            or os.environ.get("GROQ_API_KEY", "")
        )
        self.tracker: ReviewLLMTracker = get_review_tracker(self.review_id)
        self.cache: LLMStructuredCache = get_llm_cache()

        self._client = None

        if self.provider == "groq" and self.api_key and self.api_key not in ("mock_key", "your_groq_api_key_here"):
            self._init_groq_client()

        self.logger.info(f"Groq LLM initialized with model {self.model}")

    def _init_groq_client(self):
        """Initialize Groq client if library is installed and key is present."""
        if Groq is not None and self.api_key:
            try:
                self._client = Groq(api_key=self.api_key, timeout=getattr(self.settings, "GROQ_TIMEOUT", 60.0))
            except Exception as e:
                self.logger.warning(f"Could not initialize Groq Client: {e}")

    def _get_client(self):
        if self._client is None:
            if Groq is None:
                raise ImportError("groq is not installed. Please install it using 'pip install groq'.")
            effective_key = self.api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_groq_api_key_here"):
                raise ValueError("Groq API key is required when Groq LLM functionality is enabled.")
            self._client = Groq(api_key=effective_key, timeout=getattr(self.settings, "GROQ_TIMEOUT", 60.0))
        return self._client

    def generate_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Generates a structured JSON response from Groq with rate-limit awareness, caching, and fallback.
        """
        self.logger.debug(f"Structured LLM request initiated for review {self.review_id}")
        is_real_test = (
            os.environ.get("GROQ_REAL_TEST", "").lower() == "true"
            or os.environ.get("GEMINI_REAL_TEST", "").lower() == "true"
            or getattr(self.settings, "GROQ_REAL_TEST", False)
        )

        # 1. Mock mode fallback ONLY when explicitly configured
        if self.provider in ("mock", "mock_groq", "mock_gemini"):
            if is_real_test:
                raise RuntimeError("Mock provider prohibited in real test mode.")
            return self._generate_mock_structured(system_prompt, user_content)

        if not self.api_key or self.api_key in ("mock_key", "your_groq_api_key_here"):
            if self.provider == "groq" or is_real_test:
                raise ValueError("Groq API key is required when LLM_PROVIDER is 'groq'.")
            return self._generate_mock_structured(system_prompt, user_content)

        # 2. Check prompt deduplication / response cache (bypassed in real test mode)
        if not is_real_test:
            cached_response = self.cache.get(system_prompt, user_content, self.model)
            if cached_response is not None:
                self.logger.debug(f"LLM request cache hit for review {self.review_id} on model {self.model}.")
                return cached_response

        # 3. Check review-level request budget
        if not self.tracker.can_request():
            if is_real_test:
                raise RuntimeError(f"LLM request budget exhausted for review {self.review_id} in real test mode.")
            self.logger.warning(
                f"LLM request budget exhausted for review {self.review_id} "
                f"({self.tracker.requests_made}/{self.tracker.max_requests}); continuing with deterministic findings."
            )
            return None

        # 4. Determine available candidate models (strictly primary model in real test mode)
        fallback_list = getattr(
            self.settings,
            "groq_fallback_model_list",
            ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "groq/compound-mini", "llama-3.1-8b-instant"]
        )
        candidate_models = self.tracker.get_available_models(self.model, fallback_list)

        if not candidate_models:
            if is_real_test:
                raise RuntimeError(f"No candidate models available in real test mode for {self.model}.")
            self.logger.warning(f"All configured LLM models exhausted for review {self.review_id}; returning degraded review.")
            self.tracker.set_degraded_mode("all_models_exhausted")
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        max_transient_retries = 1 if is_real_test else max(1, getattr(self.settings, "LLM_MAX_RETRIES", 2))
        backoff_base = getattr(self.settings, "LLM_BACKOFF_BASE_SECONDS", 1.5)

        last_error = None
        for current_model in candidate_models:
            if self.tracker.is_model_exhausted(current_model):
                continue

            for attempt in range(1, max_transient_retries + 1):
                self.tracker.record_attempt(current_model)
                try:
                    client = self._get_client()
                    chat_completion = client.chat.completions.create(
                        messages=messages,
                        model=current_model,
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=getattr(self.settings, "LLM_MAX_TOKENS", 4096),
                    )

                    content = ""
                    if chat_completion.choices and len(chat_completion.choices) > 0:
                        content = chat_completion.choices[0].message.content or ""

                    if content:
                        cleaned_content = self._clean_json_text(content)
                        parsed = json.loads(cleaned_content)
                        if isinstance(parsed, dict):
                            parsed = self._normalize_response(parsed)
                            parsed["reasoning_source"] = "llm"
                            # Record successful request and token accounting
                            prompt_tokens = 0
                            completion_tokens = 0
                            if hasattr(chat_completion, "usage") and chat_completion.usage:
                                prompt_tokens = getattr(chat_completion.usage, "prompt_tokens", 0) or 0
                                completion_tokens = getattr(chat_completion.usage, "completion_tokens", 0) or 0
                            self.tracker.record_request()
                            self.tracker.record_success(current_model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
                            if not is_real_test:
                                self.cache.set(system_prompt, user_content, current_model, parsed)
                            return parsed

                    if is_real_test:
                        raise RuntimeError(f"Empty content returned from {self.provider} ({current_model}) in real test mode.")
                    self.logger.warning(f"Empty content returned from {self.provider} ({current_model})")
                    self.tracker.record_failure(current_model, "empty_content")
                    break

                except json.JSONDecodeError as jde:
                    if is_real_test:
                        raise RuntimeError(f"JSON decode error with model {current_model} in real test mode: {jde}") from jde
                    self.logger.error(f"JSON Decode Error with model {current_model} on attempt {attempt}: {jde}")
                    self.tracker.record_failure(current_model, f"json_decode_error: {jde}")
                    if attempt == max_transient_retries:
                        break
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    is_model_not_found = any(
                        term in err_str for term in [
                            "model_not_found", "does not exist", "do not have access", "terms acceptance", "terms_required"
                        ]
                    )
                    # Differentiate Token-Per-Day (TPD) quota from temporary request rate limit
                    is_daily_quota = any(
                        term in err_str for term in [
                            "tpd", "tokens per day", "tokens_per_day", "tpd limit",
                            "rpd", "requests per day", "requests_per_day",
                            "daily", "per_day", "quota_exceeded", "dayperproject",
                            "daily token quota", "tokens per day limit"
                        ]
                    )
                    is_rpm_rate_limit = (
                        any(term in err_str for term in ["rate_limit_exceeded", "requests per minute", "tokens per minute", "tpm", "rpm"])
                        or ("429" in err_str)
                    ) and not is_daily_quota

                    is_server_error = any(code in err_str for code in ["500", "502", "503", "504"])
                    is_auth_error = any(
                        term in err_str for term in [
                            "invalid_api_key", "unauthorized", "permission_denied", "401", "403"
                        ]
                    )

                    # Case A: Model not available on this API key -> skip to next fallback model immediately
                    if is_model_not_found:
                        self.tracker.mark_model_exhausted(current_model, "model_not_found")
                        self.tracker.record_failure(current_model, "model_not_found")
                        self.logger.warning(
                            f"Groq model {current_model} not available; skipping to next fallback model for review {self.review_id}."
                        )
                        break

                    # Case B: Permanent Daily Quota / TPD Exhaustion -> immediately switch without wasting retries
                    if is_daily_quota:
                        self.tracker.mark_model_exhausted(current_model, "daily_token_quota_exhausted")
                        self.tracker.record_failure(current_model, "daily_token_quota_exhausted")
                        self.logger.warning(
                            f"Model {current_model} exhausted daily token quota; skipping remaining retries and switching fallback."
                        )
                        break

                    # Case C: Auth Error -> Fail immediately
                    if is_auth_error:
                        self.tracker.record_failure(current_model, "auth_error")
                        self.logger.error(f"Groq authentication/configuration error: {e}")
                        if is_real_test:
                            raise RuntimeError(f"Groq authentication error: {e}") from e
                        return None

                    # Case D: Temporary RPM / TPM Rate Limit -> Bounded retry with backoff
                    if is_rpm_rate_limit:
                        if attempt < max_transient_retries:
                            sleep_time = min(3.0, backoff_base * (1.5 ** attempt) + random.uniform(0.1, 0.4))
                            self.logger.info(
                                f"Temporary Groq rate limit for {current_model} on review {self.review_id} "
                                f"(attempt {attempt}/{max_transient_retries}); retrying in {sleep_time:.1f}s."
                            )
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            self.tracker.record_failure(current_model, "rate_limit_max_retries")
                            self.logger.warning(
                                f"Temporary Groq rate limit exceeded max retries for model {current_model}; switching to next fallback model."
                            )
                            break

                    # Case E: Server Error (500 / 503) -> Bounded retry
                    if is_server_error:
                        if attempt < max_transient_retries:
                            sleep_time = backoff_base * attempt
                            self.logger.info(
                                f"Groq server error {current_model} on review {self.review_id} (attempt {attempt}); retrying in {sleep_time:.1f}s."
                            )
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.tracker.record_failure(current_model, "server_error_max_retries")
                            self.logger.warning(f"Groq server errors persisted on {current_model}; switching to next model.")
                            break

                    # Other unhandled errors
                    self.tracker.record_failure(current_model, f"error: {e}")
                    self.logger.error(f"Groq API Error with model {current_model}: {e}")
                    break

        # All candidate models failed or exhausted
        if is_real_test and last_error is not None:
            raise RuntimeError(f"Real Groq API request failed across candidate models: {last_error}") from last_error

        self.tracker.set_degraded_mode("all_models_failed")
        self.logger.warning(f"All configured Groq models failed for review {self.review_id}; returning degraded review.")
        return None

    def _normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field aliases and apply schema defaults."""
        # Flatten if nested in 'issues' list
        if "issues" in parsed and isinstance(parsed["issues"], list) and len(parsed["issues"]) > 0:
            first_issue = parsed["issues"][0]
            if isinstance(first_issue, dict):
                for k, v in first_issue.items():
                    if k not in parsed:
                        parsed[k] = v

        # Field alias normalization
        if "remediation" in parsed and "fix" not in parsed:
            parsed["fix"] = parsed["remediation"]
        if "suggestion" in parsed and "fix" not in parsed:
            parsed["fix"] = parsed["suggestion"]
        if "solution" in parsed and "fix" not in parsed:
            parsed["fix"] = parsed["solution"]
        if "explanation" in parsed and "root_cause" not in parsed:
            parsed["root_cause"] = parsed["explanation"]
        if "cause" in parsed and "root_cause" not in parsed:
            parsed["root_cause"] = parsed["cause"]
        if "trigger" in parsed and "trigger_condition" not in parsed:
            parsed["trigger_condition"] = parsed["trigger"]
        if "condition" in parsed and "trigger_condition" not in parsed:
            parsed["trigger_condition"] = parsed["condition"]
        if "runtime_condition" in parsed and "trigger_condition" not in parsed:
            parsed["trigger_condition"] = parsed["runtime_condition"]
        if "type" in parsed and "issue_type" not in parsed:
            parsed["issue_type"] = parsed["type"]
        if "category" in parsed and "issue_type" not in parsed:
            parsed["issue_type"] = parsed["category"]
        if "classification" in parsed and "issue_type" not in parsed:
            parsed["issue_type"] = parsed["classification"]

        # Defaults for schema safety
        if "trigger_condition" not in parsed:
            parsed["trigger_condition"] = parsed.get("root_cause", "Runtime execution with untrusted inputs")
        if "issue_type" not in parsed:
            parsed["issue_type"] = "security"

        parsed["reasoning_source"] = "llm"
        return parsed

    async def generate_structured_async(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously generates a structured JSON response from Groq.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_structured, system_prompt, user_content)

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code fencing if present."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _generate_mock_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Return deterministic mock responses for testing."""
        prompt_lower = system_prompt.lower()
        content_lower = user_content.lower()

        if "root cause" in prompt_lower or "root_cause" in prompt_lower:
            return {
                "root_cause": "Static analysis detected potential hazardous behavior in the highlighted code.",
                "trigger_condition": "Triggers when execution reaches this code path with untrusted inputs.",
                "fix": "Refactor the logic to sanitize inputs and use secure, parameterized methods.",
                "patch": "",
                "issue_type": "security" if "security" in content_lower or "bandit" in content_lower else "runtime_logic_error",
                "reasoning_source": "llm"
            }
        elif "bug detection" in prompt_lower or "issues" in prompt_lower:
            return {
                "issues": [
                    {
                        "line": 1,
                        "issue": "Mock finding for testing",
                        "severity": "medium",
                        "confidence": 0.9,
                        "issue_type": "bug",
                        "reasoning_source": "llm"
                    }
                ],
                "reasoning_source": "llm"
            }
        elif "fix suggestion" in prompt_lower:
            return {
                "fix_description": "Apply recommended safety patterns.",
                "patch": "",
                "reasoning_source": "llm"
            }
        return {
            "root_cause": "Static analysis flagged this line.",
            "trigger_condition": "Runtime execution of the marked line.",
            "fix": "Review and update line.",
            "patch": "",
            "issue_type": "code_smell",
            "reasoning_source": "llm"
        }
