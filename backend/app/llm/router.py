"""
CodeGuard V2 — Provider Router and Multi-Provider Orchestrator.

Routes LLM requests to primary provider (Groq) with automatic,
review-aware failover to fallback provider (Gemini).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.llm.models import LLMRequest, LLMResponse
from app.llm.providers.base import LLMProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.llm_budget import ReviewLLMTracker

logger = logging.getLogger(__name__)


class ProviderRouter:
    """
    Orchestrates multi-provider LLM routing with review-aware quota tracking,
    bounded retries, and fallback cascade.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, LLMProvider]] = None,
        primary_provider: Optional[str] = None,
        fallback_providers: Optional[List[str]] = None,
    ):
        settings = get_settings()
        self.settings = settings
        self._providers: Dict[str, LLMProvider] = {}

        if providers is not None:
            self._providers = dict(providers)
        else:
            self._init_default_providers()

        self._primary_provider_name = (
            primary_provider
            or getattr(settings, "LLM_PROVIDER", "groq")
        ).lower()

        self._fallback_provider_names = [
            p.lower()
            for p in (
                fallback_providers
                if fallback_providers is not None
                else getattr(settings, "fallback_provider_list", ["gemini"])
            )
            if p.lower() != self._primary_provider_name
        ]

    def _init_default_providers(self) -> None:
        """Initialize standard Groq and Gemini providers."""
        try:
            self._providers["groq"] = GroqProvider()
        except Exception as e:
            logger.warning(f"Could not register GroqProvider: {e}")

        try:
            self._providers["gemini"] = GeminiProvider()
        except Exception as e:
            logger.warning(f"Could not register GeminiProvider: {e}")

    def register_provider(self, provider: LLMProvider) -> None:
        """Register a custom or mock provider."""
        self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get provider instance by name."""
        return self._providers.get(name.lower())

    @property
    def primary_provider_name(self) -> str:
        return self._primary_provider_name

    @property
    def fallback_provider_names(self) -> List[str]:
        return list(self._fallback_provider_names)

    def get_eligible_providers(
        self,
        tracker: Optional[ReviewLLMTracker] = None,
    ) -> List[LLMProvider]:
        """
        Return an ordered list of providers eligible to process the request.
        Bypasses any provider marked exhausted for the current review.
        """
        candidate_names = [self._primary_provider_name] + self._fallback_provider_names
        eligible: List[LLMProvider] = []

        for name in candidate_names:
            provider = self._providers.get(name)
            if provider is None:
                continue

            # Review-aware state: if provider is exhausted for this review, bypass it!
            if tracker is not None and hasattr(tracker, "is_provider_exhausted") and tracker.is_provider_exhausted(name):
                logger.debug(f"Provider '{name}' bypassed: marked exhausted for review {getattr(tracker, 'review_id', '')}.")
                continue

            if provider.is_available():
                eligible.append(provider)

        return eligible

    def route_request(
        self,
        request: LLMRequest,
        tracker: Optional[ReviewLLMTracker] = None,
        structured: bool = True,
    ) -> LLMResponse:
        """
        Execute request against primary provider; on quota exhaustion or failure,
        transparently fail over to configured fallback providers.
        """
        eligible = self.get_eligible_providers(tracker=tracker)

        if not eligible:
            logger.warning("No eligible LLM providers available for request.")
            return LLMResponse(
                text="",
                provider="none",
                model="none",
                error="No available LLM providers configured or eligible."
            )

        last_response: Optional[LLMResponse] = None
        primary_name = self._primary_provider_name

        for idx, provider in enumerate(eligible):
            is_fallback = (idx > 0 or provider.name.lower() != primary_name)

            if is_fallback:
                logger.info(
                    f"Attempting fallback provider: '{provider.name}' for model '{provider.primary_model}'."
                )
                if tracker is not None and hasattr(tracker, "record_provider_fallback"):
                    prev_name = eligible[idx - 1].name if idx > 0 else primary_name
                    tracker.record_provider_fallback(prev_name, provider.name)

            logger.debug(f"Routing request to provider '{provider.name}' (model: {provider.primary_model}).")

            if structured:
                resp = provider.generate_structured(request, tracker=tracker)
            else:
                resp = provider.generate(request, tracker=tracker)

            if resp.is_success:
                if is_fallback:
                    resp.fallback_used = True
                    logger.info(f"Fallback to provider '{provider.name}' succeeded with model '{resp.model}'.")
                return resp

            last_response = resp
            err_msg = resp.error or "Unknown error"
            logger.warning(
                f"Provider '{provider.name}' failed request: {err_msg}."
            )

            # If quota exhausted, ensure provider is permanently blacklisted for this review
            if "quota_exhausted" in err_msg.lower() or "tpd" in err_msg.lower():
                if tracker is not None and hasattr(tracker, "mark_provider_exhausted"):
                    tracker.mark_provider_exhausted(provider.name, "quota_exhausted")
                logger.info(f"Switching provider: {provider.name} -> next available fallback.")

        # If all providers fail, return last response
        return last_response or LLMResponse(
            text="",
            provider="none",
            model="none",
            error="All eligible LLM providers failed."
        )
