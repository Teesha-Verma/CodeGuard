"""
CodeGuard V2 — Grounded Multi-Provider LLM Client.

Provider-agnostic LLM client supporting Groq (primary) and Google Gemini (fallback)
with JSON structured output, rate-limit awareness, review-level request budgeting,
prompt deduplication/caching, and multi-provider failover cascade.
"""
from __future__ import annotations

import json
import logging
import os
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
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.router import ProviderRouter
from app.llm.service import LLMService

logger = logging.getLogger(__name__)


class LLMClient:
    """Provider-oriented LLM client for generating structured review insights across Groq and Gemini."""

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

        # Providers and routing
        self._groq_provider = GroqProvider(api_key=self.api_key, primary_model=self.model)
        self._gemini_provider = GeminiProvider()

        self.router = ProviderRouter(
            providers={"groq": self._groq_provider, "gemini": self._gemini_provider},
            primary_provider=self.provider,
            fallback_providers=getattr(self.settings, "fallback_provider_list", ["gemini"])
        )
        self.service = LLMService(router=self.router, cache=self.cache)
        self._client = None

        self.logger.info(f"Multi-provider LLM initialized (Primary: {self.provider}, Model: {self.model})")

    def _sync_injected_state(self) -> None:
        """Sync any test-injected attributes (like mock client or custom provider) to router providers."""
        # Sync provider selection
        if self.provider and self.provider != self.router.primary_provider_name:
            self.router._primary_provider_name = self.provider.lower()

        # Sync injected client (frequently done in mock tests: client._client = mock_groq_client)
        if self._client is not None:
            active_p = self.router.get_provider(self.provider)
            if active_p is not None:
                active_p._client = self._client

        # Sync API key if updated directly on instance
        if self.api_key:
            active_p = self.router.get_provider(self.provider)
            if active_p is not None:
                active_p._api_key = self.api_key

    def generate_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Generates a structured JSON response with rate-limit awareness, caching, and automatic fallback.
        """
        self._sync_injected_state()

        # Check mock provider explicitly configured
        is_real_test = (
            os.environ.get("GROQ_REAL_TEST", "").lower() == "true"
            or os.environ.get("GEMINI_REAL_TEST", "").lower() == "true"
            or getattr(self.settings, "GROQ_REAL_TEST", False)
            or getattr(self.settings, "GEMINI_REAL_TEST", False)
        )
        if self.provider in ("mock", "mock_groq", "mock_gemini"):
            if is_real_test:
                raise RuntimeError("Mock provider prohibited in real test mode.")
            return self._generate_mock_structured(system_prompt, user_content)

        # Check API key requirement when primary is groq and no mock client injected
        if self._client is None and self.provider == "groq" and (not self.api_key or self.api_key in ("mock_key", "your_groq_api_key_here")):
            if is_real_test:
                raise ValueError("Groq API key is required when LLM_PROVIDER is 'groq'.")
            return self._generate_mock_structured(system_prompt, user_content)

        return self.service.generate_structured(
            system_prompt=system_prompt,
            user_content=user_content,
            review_id=self.review_id
        )

    async def generate_structured_async(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Asynchronously generates a structured JSON response."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_structured, system_prompt, user_content)

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code fencing if present."""
        return self.service.router.get_provider("groq").clean_json_text(text) if self.router.get_provider("groq") else text.strip()

    def _normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field aliases and apply schema defaults."""
        return self.service._normalize_response(parsed)

    def _generate_mock_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Return deterministic mock responses for testing."""
        return self.service._generate_mock_structured(system_prompt, user_content)
