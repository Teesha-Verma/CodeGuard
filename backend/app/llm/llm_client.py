"""
CodeGuard V2 — Grounded Gemini LLM Client.

Provider-oriented LLM client supporting Google Gemini (gemini-2.5-flash)
with JSON structured output, quota-aware error handling, review-level request
budgeting, prompt deduplication, and multi-model fallback cascade.
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
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import get_settings
from app.core.logger import PipelineLogger
from app.llm.llm_budget import get_review_tracker, ReviewLLMTracker
from app.llm.llm_cache import get_llm_cache, LLMStructuredCache


class LLMClient:
    """Provider-oriented LLM client for generating structured review insights with Gemini."""

    def __init__(self, review_id: str = ""):
        self.settings = get_settings()
        self.review_id = review_id or f"session_{uuid.uuid4().hex[:8]}"
        self.logger = PipelineLogger(review_id=self.review_id, stage="llm_client")
        self.provider = self.settings.LLM_PROVIDER
        self.model = self.settings.GEMINI_PRIMARY_MODEL or self.settings.GEMINI_LLM_MODEL or self.settings.LLM_MODEL or "gemini-2.5-flash"
        self.api_key = self.settings.GEMINI_API_KEY or self.settings.LLM_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.base_url = self.settings.GEMINI_API_BASE_URL
        self.tracker: ReviewLLMTracker = get_review_tracker(self.review_id)
        self.cache: LLMStructuredCache = get_llm_cache()

        self._client = None
        self._async_client = None

        if self.provider == "gemini" and self.api_key and self.api_key not in ("mock_key", "your_gemini_api_key_here"):
            self._init_genai_client()

        self.logger.info(f"Gemini LLM initialized with model {self.model}")

    def _init_genai_client(self):
        """Initialize Google GenAI client if library is installed."""
        if genai is not None and self.api_key:
            http_options = None
            if self.base_url and "googleapis.com" not in self.base_url:
                http_options = types.HttpOptions(base_url=self.base_url) if types else None
            try:
                self._client = genai.Client(api_key=self.api_key, http_options=http_options)
            except Exception as e:
                self.logger.warning(f"Could not initialize Google GenAI Client: {e}")

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai is not installed. Please install it using 'pip install google-genai'.")
            effective_key = self.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_gemini_api_key_here"):
                raise ValueError("Gemini API key is required when Gemini LLM functionality is enabled.")
            self._client = genai.Client(api_key=effective_key)
        return self._client

    def generate_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Generates a structured JSON response from Gemini with quota awareness, caching, and fallback.
        """
        self.logger.debug(f"Structured LLM request initiated for review {self.review_id}")
        is_real_test = os.environ.get("GEMINI_REAL_TEST", "").lower() == "true" or getattr(self.settings, "GEMINI_REAL_TEST", False)

        # 1. Mock mode fallback ONLY when explicitly configured (prohibited in real test mode)
        if self.provider in ("mock", "mock_gemini"):
            if is_real_test:
                raise RuntimeError("Mock provider prohibited in GEMINI_REAL_TEST mode.")
            return self._generate_mock_structured(system_prompt, user_content)

        if not self.api_key or self.api_key in ("mock_key", "your_gemini_api_key_here"):
            if self.provider == "gemini" or is_real_test:
                raise ValueError("Gemini API key is required when LLM_PROVIDER is 'gemini'.")
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
        if is_real_test:
            candidate_models = [self.model]
        else:
            fallback_list = self.settings.gemini_fallback_model_list
            candidate_models = self.tracker.get_available_models(self.model, fallback_list)

        if not candidate_models:
            if is_real_test:
                raise RuntimeError(f"No candidate models available in real test mode for {self.model}.")
            self.logger.warning(f"All configured LLM models exhausted for review {self.review_id}; returning degraded review.")
            self.tracker.set_degraded_mode("all_models_exhausted")
            return None

        gen_config = None
        if types is not None:
            config_kwargs = {
                "response_mime_type": "application/json",
            }
            if system_prompt:
                config_kwargs["system_instruction"] = system_prompt
            if hasattr(types, "AutomaticFunctionCallingConfig"):
                config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
            gen_config = types.GenerateContentConfig(**config_kwargs)

        max_transient_retries = 1 if is_real_test else max(1, self.settings.LLM_MAX_RETRIES or 2)
        backoff_base = self.settings.LLM_BACKOFF_BASE_SECONDS or 1.5

        for current_model in candidate_models:
            if not is_real_test and self.tracker.is_model_exhausted(current_model):
                continue

            for attempt in range(1, max_transient_retries + 1):
                try:
                    client = self._get_client()
                    response = client.models.generate_content(
                        model=current_model,
                        contents=user_content,
                        config=gen_config,
                    )

                    content = response.text if hasattr(response, "text") else str(response)
                    if content:
                        cleaned_content = self._clean_json_text(content)
                        parsed = json.loads(cleaned_content)
                        if isinstance(parsed, dict):
                            parsed = self._normalize_response(parsed)
                            # Record successful request in budget and cache
                            self.tracker.record_request()
                            if not is_real_test:
                                self.cache.set(system_prompt, user_content, current_model, parsed)
                            return parsed

                    if is_real_test:
                        raise RuntimeError(f"Empty content returned from {self.provider} ({current_model}) in real test mode.")
                    self.logger.warning(f"Empty content returned from {self.provider} ({current_model})")
                    break

                except json.JSONDecodeError as jde:
                    if is_real_test:
                        raise RuntimeError(f"JSON decode error with model {current_model} in real test mode: {jde}") from jde
                    self.logger.error(f"JSON Decode Error with model {current_model} on attempt {attempt}: {jde}")
                    if attempt == max_transient_retries:
                        break
                except Exception as e:
                    if is_real_test:
                        raise RuntimeError(f"Real Gemini API request failed on {current_model}: {e}") from e

                    err_str = str(e).lower()
                    is_daily_quota = any(
                        term in err_str for term in [
                            "generaterequestsperday", "requests_per_day", "daily", "perday", "dayperproject"
                        ]
                    )
                    is_rpm_rate_limit = any(
                        term in err_str for term in [
                            "generaterequestsperminute", "requests_per_minute", "perminute", "minuteperproject"
                        ]
                    ) or ("429" in err_str and not is_daily_quota)
                    is_server_error = any(code in err_str for code in ["500", "502", "503", "504"])
                    is_auth_error = any(
                        term in err_str for term in [
                            "api_key_invalid", "unregistered", "permission_denied", "401", "403"
                        ]
                    )

                    # Case A: Permanent Daily Quota Exhaustion -> 0 retries on this model
                    if is_daily_quota:
                        self.tracker.mark_model_exhausted(current_model, "daily_quota_exhausted")
                        self.logger.warning(
                            f"Gemini daily quota exhausted for model {current_model}; skipping model for remainder of review {self.review_id}."
                        )
                        break  # Move immediately to next model in candidate_models

                    # Case B: Auth/Configuration Error -> Fail immediately
                    if is_auth_error:
                        self.logger.error(f"Gemini authentication/configuration error: {e}")
                        return None

                    # Case C: Temporary RPM Rate Limit -> Bounded retry with jitter
                    if is_rpm_rate_limit:
                        if attempt < max_transient_retries:
                            sleep_time = min(3.0, backoff_base * (1.5 ** attempt) + random.uniform(0.1, 0.4))
                            self.logger.info(
                                f"Temporary Gemini rate limit for {current_model} on review {self.review_id} "
                                f"(attempt {attempt}/{max_transient_retries}); retrying in {sleep_time:.1f}s."
                            )
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            self.logger.warning(
                                f"Temporary Gemini rate limit exceeded max retries for model {current_model}; switching to next fallback model."
                            )
                            break

                    # Case D: Server Error (503 / 500) -> Bounded retry
                    if is_server_error:
                        if attempt < max_transient_retries:
                            sleep_time = backoff_base * attempt
                            self.logger.info(
                                f"Gemini server error {current_model} on review {self.review_id} (attempt {attempt}); retrying in {sleep_time:.1f}s."
                            )
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.logger.warning(f"Gemini server errors persisted on {current_model}; switching to next model.")
                            break

                    # Other unhandled errors
                    self.logger.error(f"Gemini API Error with model {current_model}: {e}")
                    break

        # All candidate models failed or exhausted
        self.tracker.set_degraded_mode("all_models_failed")
        self.logger.warning(f"All configured LLM models failed for review {self.review_id}; returning degraded review.")
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

        return parsed

    async def generate_structured_async(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously generates a structured JSON response from Gemini.
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
                "issue_type": "security" if "security" in content_lower or "bandit" in content_lower else "runtime_logic_error"
            }
        elif "bug detection" in prompt_lower or "issues" in prompt_lower:
            return {
                "issues": [
                    {
                        "line": 1,
                        "issue": "Mock finding for testing",
                        "severity": "medium",
                        "confidence": 0.9,
                        "issue_type": "bug"
                    }
                ]
            }
        elif "fix suggestion" in prompt_lower:
            return {
                "fix_description": "Apply recommended safety patterns.",
                "patch": ""
            }
        return {
            "root_cause": "Static analysis flagged this line.",
            "trigger_condition": "Runtime execution of the marked line.",
            "fix": "Review and update line.",
            "patch": "",
            "issue_type": "code_smell"
        }
