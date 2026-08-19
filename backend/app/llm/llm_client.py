"""
CodeGuard V2 — Grounded Gemini LLM Client.

Provider-oriented LLM client supporting Google Gemini (gemini-3.6-flash)
with JSON structured output, retry resilience, and offline test fallback.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import get_settings
from app.core.logger import PipelineLogger


class LLMClient:
    """Provider-oriented LLM client for generating structured review insights with Gemini."""

    def __init__(self, review_id: str = ""):
        self.settings = get_settings()
        self.review_id = review_id
        self.logger = PipelineLogger(review_id=review_id, stage="llm_client")
        self.provider = self.settings.LLM_PROVIDER
        self.model = self.settings.GEMINI_LLM_MODEL or self.settings.LLM_MODEL or "gemini-3.6-flash"
        self.api_key = self.settings.GEMINI_API_KEY or self.settings.LLM_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.base_url = self.settings.GEMINI_API_BASE_URL

        self._client = None
        self._async_client = None

        if self.provider == "gemini" and self.api_key and self.api_key not in ("mock_key", "your_gemini_api_key_here"):
            self._init_genai_client()

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
        Generates a structured JSON response from Gemini.
        Synchronous interface called by the review pipeline and root-cause engine.
        Omit deprecated sampling parameters (temperature, top_p, top_k) for Gemini 3.6 Flash.
        """
        self.logger.debug(f"Sending structured request to {self.provider} ({self.model})")

        # Mock mode fallback for testing without real credentials
        if self.provider in ("mock", "mock_gemini") or not self.api_key or self.api_key in ("mock_key", "your_gemini_api_key_here"):
            return self._generate_mock_structured(system_prompt, user_content)

        max_retries = self.settings.GEMINI_MAX_RETRIES or self.settings.LLM_MAX_RETRIES or 3
        backoff_factor = 2.0

        gen_config = None
        if types is not None:
            config_kwargs = {
                "response_mime_type": "application/json",
            }
            if system_prompt:
                config_kwargs["system_instruction"] = system_prompt
            gen_config = types.GenerateContentConfig(**config_kwargs)

        for attempt in range(1, max_retries + 1):
            try:
                client = self._get_client()
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_content,
                    config=gen_config,
                )

                content = response.text if hasattr(response, "text") else str(response)
                if content:
                    cleaned_content = self._clean_json_text(content)
                    return json.loads(cleaned_content)

                self.logger.warning(f"Empty content returned from {self.provider}")
                return None

            except json.JSONDecodeError as jde:
                self.logger.error(f"JSON Decode Error on attempt {attempt}/{max_retries}: {jde}")
                if attempt == max_retries:
                    return None
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(code in err_str for code in ["429", "500", "502", "503", "504", "timeout", "connection", "rate limit", "resource_exhausted"])
                self.logger.warning(f"Gemini API Error on attempt {attempt}/{max_retries}: {e}")
                if not is_transient or attempt == max_retries:
                    self.logger.error(f"Non-transient or final API Error: {e}")
                    return None

            sleep_time = backoff_factor ** attempt
            time.sleep(sleep_time)

        return None

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
