"""
CodeGuard V2 — Unified LLM Service.

Coordinates caching, review request budgeting, multi-provider routing,
and structured response normalization.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.llm.llm_budget import ReviewLLMTracker, get_review_tracker
from app.llm.llm_cache import LLMStructuredCache, get_llm_cache
from app.llm.models import LLMRequest, LLMResponse
from app.llm.router import ProviderRouter

logger = logging.getLogger(__name__)


class LLMService:
    """
    Central LLM reasoning service providing provider-agnostic structured generation,
    caching, shared review budget enforcement, and fallback orchestration.
    """

    def __init__(
        self,
        router: Optional[ProviderRouter] = None,
        cache: Optional[LLMStructuredCache] = None,
    ):
        self.settings = get_settings()
        self.router = router or ProviderRouter()
        self.cache = cache or get_llm_cache()

    def generate_structured(
        self,
        system_prompt: str,
        user_content: str,
        review_id: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Generates a structured JSON response from the active LLM provider cascade
        with cache check, budget enforcement, and fallback.
        """
        review_id = review_id or "default"
        tracker: ReviewLLMTracker = get_review_tracker(review_id)

        is_real_test = (
            os.environ.get("GROQ_REAL_TEST", "").lower() == "true"
            or os.environ.get("GEMINI_REAL_TEST", "").lower() == "true"
            or getattr(self.settings, "GROQ_REAL_TEST", False)
            or getattr(self.settings, "GEMINI_REAL_TEST", False)
        )

        # 1. Mock mode fallback ONLY when explicitly configured
        provider_name = getattr(self.settings, "LLM_PROVIDER", "groq").lower()
        if provider_name in ("mock", "mock_groq", "mock_gemini"):
            if is_real_test:
                raise RuntimeError("Mock provider prohibited in real test mode.")
            return self._generate_mock_structured(system_prompt, user_content)

        # 2. Check prompt deduplication / cache (bypassed in real test mode)
        cache_key_model = self.router.primary_provider_name
        if not is_real_test:
            cached_response = self.cache.get(system_prompt, user_content, cache_key_model)
            if cached_response is not None:
                logger.debug(f"LLM request cache hit for review {review_id}.")
                return cached_response

        # 3. Check review-level shared request budget
        if not tracker.can_request():
            if is_real_test:
                raise RuntimeError(f"LLM request budget exhausted for review {review_id} in real test mode.")
            logger.warning(
                f"LLM request budget exhausted for review {review_id} "
                f"({tracker.requests_made}/{tracker.max_requests}); falling back to static analysis."
            )
            return None

        # Build normalized request
        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_content,
            temperature=0.2,
            max_tokens=getattr(self.settings, "LLM_MAX_TOKENS", 4096),
            response_format="json",
            timeout=getattr(self.settings, "LLM_TIMEOUT", 60.0),
            metadata={"review_id": review_id}
        )

        # 4. Route request through ProviderRouter (Groq -> Gemini fallback)
        response: LLMResponse = self.router.route_request(
            request=request,
            tracker=tracker,
            structured=True
        )

        if response.is_success and response.parsed_json is not None:
            # Deduct from review-level shared budget exactly once per logical finding
            tracker.record_request()

            normalized = self._normalize_response(response.parsed_json)
            normalized["reasoning_source"] = "llm"
            normalized["llm_provider"] = response.provider
            normalized["llm_model"] = response.model
            if response.fallback_used:
                normalized["fallback_used"] = True

            if not is_real_test:
                self.cache.set(system_prompt, user_content, cache_key_model, normalized)

            return normalized

        if is_real_test and response.error:
            raise RuntimeError(f"Real LLM request failed across providers: {response.error}")

        logger.warning(
            f"All LLM providers failed for review {review_id}: {response.error}. "
            f"Continuing with deterministic findings."
        )
        if tracker is not None and hasattr(tracker, "set_degraded_mode"):
            tracker.set_degraded_mode("all_models_failed")
        return None

    def _normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field aliases and apply schema defaults."""
        if "issues" in parsed and isinstance(parsed["issues"], list) and len(parsed["issues"]) > 0:
            first_issue = parsed["issues"][0]
            if isinstance(first_issue, dict):
                for k, v in first_issue.items():
                    if k not in parsed:
                        parsed[k] = v

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

        if "trigger_condition" not in parsed:
            parsed["trigger_condition"] = parsed.get("root_cause", "Runtime execution with untrusted inputs")
        if "issue_type" not in parsed:
            parsed["issue_type"] = "security"

        parsed["reasoning_source"] = "llm"
        return parsed

    def _generate_mock_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Return deterministic mock responses for testing."""
        prompt_lower = system_prompt.lower()
        content_lower = user_content.lower()

        provider = "mock"
        model = "mock-model"

        if "root cause" in prompt_lower or "root_cause" in prompt_lower:
            return {
                "root_cause": "Static analysis detected potential hazardous behavior in the highlighted code.",
                "trigger_condition": "Triggers when execution reaches this code path with untrusted inputs.",
                "fix": "Refactor the logic to sanitize inputs and use secure, parameterized methods.",
                "patch": "",
                "issue_type": "security" if "security" in content_lower or "bandit" in content_lower else "runtime_logic_error",
                "reasoning_source": "llm",
                "llm_provider": provider,
                "llm_model": model,
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
                        "reasoning_source": "llm",
                    }
                ],
                "reasoning_source": "llm",
                "llm_provider": provider,
                "llm_model": model,
            }
        elif "fix suggestion" in prompt_lower:
            return {
                "fix_description": "Apply recommended safety patterns.",
                "patch": "",
                "reasoning_source": "llm",
                "llm_provider": provider,
                "llm_model": model,
            }
        return {
            "root_cause": "Static analysis flagged this line.",
            "trigger_condition": "Runtime execution of the marked line.",
            "fix": "Review and update line.",
            "patch": "",
            "issue_type": "code_smell",
            "reasoning_source": "llm",
            "llm_provider": provider,
            "llm_model": model,
        }

    def health_status(self) -> Dict[str, Any]:
        """Return non-sensitive status of configured LLM providers."""
        groq_provider = self.router.get_provider("groq")
        gemini_provider = self.router.get_provider("gemini")

        return {
            "primary_provider": self.router.primary_provider_name,
            "fallback_providers": self.router.fallback_provider_names,
            "groq_configured": bool(groq_provider and groq_provider.is_available()),
            "gemini_llm_configured": bool(gemini_provider and gemini_provider.is_available()),
            "gemini_embeddings_configured": bool(
                self.settings.GEMINI_API_KEY
                and self.settings.GEMINI_API_KEY not in ("mock_key", "your_gemini_api_key_here")
            ),
        }
