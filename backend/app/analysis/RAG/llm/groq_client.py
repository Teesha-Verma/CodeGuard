"""
Groq API client implementation for RAG and synthesis.
"""
from __future__ import annotations

import os
import json
import random
import time
import uuid
import logging
from typing import Any, Optional

try:
    import groq
    from groq import Groq
except ImportError:
    groq = None
    Groq = None

from .base_client import BaseLLMClient
from ..responses.review_schema import ReviewResponse
from ..retry.retry_engine import RetryEngine
from ..telemetry.llm_telemetry import LLMTelemetryManager, LLMUsageMetrics
from app.llm.llm_budget import get_review_tracker, ReviewLLMTracker
from app.llm.llm_cache import get_llm_cache, LLMStructuredCache

logger = logging.getLogger(__name__)


class GroqClient(BaseLLMClient):
    """
    Client for Groq API using the official Groq Python SDK.
    Primary model: llama-3.3-70b-versatile
    Fallback model: llama-3.1-8b-instant
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are an expert code reviewer. Analyze the code and output a JSON object adhering to this schema:\n"
        "{\n"
        '  "review_summary": "<summary of findings>",\n'
        '  "overall_severity": "<low|medium|high|critical>",\n'
        '  "findings": [\n'
        '    {\n'
        '      "title": "<finding title>",\n'
        '      "severity": "<low|medium|high|critical>",\n'
        '      "file_path": "<file path or snippet>",\n'
        '      "line_number": 1,\n'
        '      "evidence": "<code snippet evidence>",\n'
        '      "reasoning": "<why this is an issue>",\n'
        '      "priority": "<low|medium|high|critical>",\n'
        '      "remediation": "<how to fix>",\n'
        '      "code_suggestion": "<suggested code>",\n'
        '      "references": []\n'
        '    }\n'
        '  ],\n'
        '  "evidence_summary": "<summary of evidence>",\n'
        '  "reasoning_trace": "<reasoning explanation>",\n'
        '  "confidence": 0.95,\n'
        '  "priority": "<low|medium|high|critical>",\n'
        '  "remediation_summary": "<remediation overview>",\n'
        '  "code_suggestions": [],\n'
        '  "references": [],\n'
        '  "review_metadata": {}\n'
        "}"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        config: Any = None,
        telemetry: Optional[LLMTelemetryManager] = None,
        review_id: str = "",
    ):
        """
        Initialize the Groq client.
        """
        if config is not None:
            self.config = config
            self.api_key = getattr(config, "api_key", None) or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
            self.model = getattr(config, "model", None) or self.DEFAULT_MODEL
        else:
            self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
            self.model = model or os.environ.get("GROQ_LLM_MODEL") or os.environ.get("LLM_MODEL") or self.DEFAULT_MODEL
            from ..config.llm_config import GroqConfig
            self.config = GroqConfig(api_key=self.api_key, model=self.model)

        self.review_id = review_id if review_id and review_id != "default" else f"session_{uuid.uuid4().hex[:8]}"
        self.api_url = api_url
        self.telemetry = telemetry or LLMTelemetryManager()
        self.retry_engine = RetryEngine()
        self.tracker: ReviewLLMTracker = get_review_tracker(self.review_id)
        self.cache: LLMStructuredCache = get_llm_cache()

        self._client = None
        if Groq is not None and self.api_key and self.api_key not in ("mock_key", "your_groq_api_key_here"):
            try:
                self._client = Groq(api_key=self.api_key, timeout=60.0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq Client: {e}")

        logger.info(f"Groq LLM initialized with model {self.model}")

    @property
    def provider_name(self) -> str:
        return "groq"

    def _get_client(self):
        if self._client is None:
            if Groq is None:
                raise ImportError("groq is not installed. Please install it using 'pip install groq'.")
            effective_key = self.api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_groq_api_key_here"):
                raise ValueError("Groq API key is required when Groq LLM functionality is enabled.")
            self._client = Groq(api_key=effective_key, timeout=60.0)
        return self._client

    def generate_review(
        self,
        prompt: Any = None,
        config: Any = None,
        query: Optional[str] = None,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ReviewResponse:
        """
        Generate a structured code review using the Groq API.
        """
        target_model = model or (config.get("model") if isinstance(config, dict) else (getattr(config, "model", None) if config else None)) or self.model or self.DEFAULT_MODEL

        # Extract system instruction and user content from prompt or query
        sys_inst = system_instruction
        user_content = ""

        if prompt is not None:
            if hasattr(prompt, "system_instruction") and hasattr(prompt, "user_prompt"):
                sys_inst = sys_inst or prompt.system_instruction
                user_content = prompt.user_prompt
            elif isinstance(prompt, list):
                for m in prompt:
                    if isinstance(m, dict) and m.get("role") == "system":
                        sys_inst = sys_inst or m.get("content", "")
                    elif isinstance(m, dict) and m.get("role") == "user":
                        user_content = m.get("content", "")
            elif isinstance(prompt, dict):
                sys_inst = sys_inst or prompt.get("system_instruction", "")
                user_content = prompt.get("user_prompt", prompt.get("prompt", str(prompt)))
            else:
                user_content = str(prompt)
        elif query is not None:
            user_content = f"Context:\n{context}\n\nQuery:\n{query}" if context else query

        sys_inst = sys_inst or self.DEFAULT_SYSTEM_INSTRUCTION
        system_instruction = sys_inst

        is_real_test = (
            os.environ.get("GROQ_REAL_TEST", "").lower() == "true"
            or os.environ.get("GEMINI_REAL_TEST", "").lower() == "true"
        )

        # Check response cache (bypassed in real test mode)
        if not is_real_test:
            cached = self.cache.get(system_instruction, user_content, target_model)
            if cached is not None:
                logger.debug(f"GroqClient cache hit for review {self.review_id}")
                return ReviewResponse.model_validate(cached)

        # Check request budget
        if not self.tracker.can_request():
            if is_real_test:
                raise RuntimeError("LLM request budget exhausted in real test mode.")
            logger.warning(
                f"LLM request budget exhausted ({self.tracker.requests_made}/{self.tracker.max_requests}) "
                f"for review {self.review_id}; returning degraded response."
            )
            return self._build_degraded_review("LLM request budget exhausted; review generated from deterministic findings.")

        # Determine candidate models
        fallback_models = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "groq/compound-mini", "llama-3.1-8b-instant"]
        candidate_models = self.tracker.get_available_models(target_model, fallback_models)

        if not candidate_models:
            if is_real_test:
                raise RuntimeError("All configured Groq models exhausted in real test mode.")
            logger.warning(f"All configured Groq models exhausted for review {self.review_id}; returning degraded review.")
            self.tracker.set_degraded_mode("all_models_exhausted")
            return self._build_degraded_review("All Groq models exhausted; review generated from deterministic findings.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": user_content})

        max_transient_retries = 1 if is_real_test else 2
        last_error = None

        for current_model in candidate_models:
            if self.tracker.is_model_exhausted(current_model):
                continue

            for attempt in range(1, max_transient_retries + 1):
                start_time = time.time()
                try:
                    client = self._get_client()
                    chat_completion = client.chat.completions.create(
                        messages=messages,
                        model=current_model,
                        response_format={"type": "json_object"},
                        temperature=temperature or 0.2,
                        max_tokens=max_tokens or 4096,
                    )

                    content = ""
                    if chat_completion.choices and len(chat_completion.choices) > 0:
                        content = chat_completion.choices[0].message.content or ""

                    latency_ms = (time.time() - start_time) * 1000
                    cleaned_content = self._clean_json_text(content)
                    parsed_json = json.loads(cleaned_content)
                    if not isinstance(parsed_json, dict):
                        parsed_json = {"review_summary": str(parsed_json)}

                    parsed_json = self._normalize_review_payload(parsed_json)
                    self.tracker.record_request()
                    if not is_real_test:
                        self.cache.set(system_instruction, user_content, current_model, parsed_json)

                    self.telemetry.record_request(
                        LLMUsageMetrics(
                            provider="groq",
                            model_name=current_model,
                            prompt_tokens=getattr(chat_completion.usage, "prompt_tokens", 0) if hasattr(chat_completion, "usage") and chat_completion.usage else 0,
                            completion_tokens=getattr(chat_completion.usage, "completion_tokens", 0) if hasattr(chat_completion, "usage") and chat_completion.usage else 0,
                            latency_ms=latency_ms,
                            success=True,
                            review_id=self.review_id,
                        )
                    )

                    return ReviewResponse.model_validate(parsed_json)

                except json.JSONDecodeError as jde:
                    if is_real_test:
                        raise RuntimeError(f"JSON decode error with model {current_model} in real test mode: {jde}") from jde
                    logger.error(f"JSON Decode Error on attempt {attempt} with model {current_model}: {jde}")
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
                    is_daily_quota = any(term in err_str for term in ["daily", "quota_exceeded", "per_day"])
                    is_rpm_limit = any(term in err_str for term in ["rate_limit_exceeded", "rpm", "tpm"]) or ("429" in err_str and not is_daily_quota)
                    is_auth_error = any(term in err_str for term in ["invalid_api_key", "unauthorized", "401", "403"])

                    if is_model_not_found:
                        self.tracker.mark_model_exhausted(current_model, "model_not_found")
                        logger.warning(f"Groq model {current_model} not available; skipping to next fallback for review {self.review_id}.")
                        break

                    if is_daily_quota:
                        self.tracker.mark_model_exhausted(current_model, "daily_quota_exhausted")
                        logger.warning(f"Groq daily quota exhausted for model {current_model}; skipping for review {self.review_id}.")
                        break

                    if is_auth_error:
                        logger.error(f"Groq auth error on model {current_model}: {e}")
                        if is_real_test:
                            raise RuntimeError(f"Groq auth error: {e}") from e
                        break

                    if is_rpm_limit:
                        if attempt < max_transient_retries:
                            sleep_time = min(3.0, 1.5 * attempt + random.uniform(0.1, 0.4))
                            logger.info(f"Temporary Groq rate limit on {current_model} (attempt {attempt}); retrying in {sleep_time:.1f}s.")
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            logger.warning(f"Groq rate limit persisted on {current_model}; moving to next model.")
                            break

                    logger.error(f"Groq API Error on {current_model}: {e}")
                    break

        if is_real_test and last_error is not None:
            raise RuntimeError(f"Real Groq API request failed across all candidate models: {last_error}") from last_error

        self.tracker.set_degraded_mode("all_models_failed")
        logger.warning(f"All configured Groq models failed for review {self.review_id}; returning degraded review.")
        return self._build_degraded_review("Groq generation failed; review generated from deterministic findings.")

    def generate_raw(self, prompt_text: str, system_instruction: str = "") -> str:
        """
        Generate raw text completion from Groq.
        """
        client = self._get_client()
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt_text})

        resp = client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=0.2,
            max_tokens=4096,
        )
        if resp.choices and len(resp.choices) > 0:
            return resp.choices[0].message.content or ""
        return ""

    def _normalize_review_payload(self, data: dict) -> dict:
        """Normalize JSON payload keys and ensure types conform to ReviewResponse schema."""
        if "overall_severity" not in data:
            data["overall_severity"] = "medium"

        if "findings" not in data or not isinstance(data["findings"], list):
            data["findings"] = []

        for f in data.get("findings", []):
            if isinstance(f, dict):
                if "references" in f and isinstance(f["references"], str):
                    f["references"] = [ref.strip() for ref in f["references"].split(",") if ref.strip()]
                elif "references" not in f or not isinstance(f.get("references"), list):
                    f["references"] = []
                if "line_number" in f:
                    try:
                        f["line_number"] = int(f["line_number"])
                    except (ValueError, TypeError):
                        f["line_number"] = 1

        for list_key in ["code_suggestions", "references"]:
            if list_key in data and isinstance(data[list_key], str):
                data[list_key] = [data[list_key]]
            elif list_key not in data or not isinstance(data[list_key], list):
                data[list_key] = []

        if "confidence" in data:
            try:
                data["confidence"] = float(data["confidence"])
            except (ValueError, TypeError):
                data["confidence"] = 0.90

        if "priority" not in data:
            data["priority"] = "medium"

        return data

    def _build_degraded_review(self, reason: str) -> ReviewResponse:
        """Build a deterministic fallback ReviewResponse."""
        return ReviewResponse(
            review_summary=reason,
            overall_severity="low",
            findings=[],
            evidence_summary="Deterministic analysis completed without LLM reasoning.",
            reasoning_trace="Static rule evaluation applied.",
            confidence=0.70,
            priority="low",
            remediation_summary="Review completed via deterministic analysis rules.",
            code_suggestions=[],
            references=[],
            review_metadata={"degraded_mode": True, "reason": reason, "provider": "groq"},
        )

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown fencing."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
