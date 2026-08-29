"""
Google Gemini API client implementation.
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
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from .base_client import BaseLLMClient
from ..responses.review_schema import ReviewResponse
from ..retry.retry_engine import RetryEngine
from ..telemetry.llm_telemetry import LLMTelemetryManager, LLMUsageMetrics
from app.llm.llm_budget import get_review_tracker, ReviewLLMTracker
from app.llm.llm_cache import get_llm_cache, LLMStructuredCache

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """
    Client for Google Gemini API using the official Google GenAI SDK.
    Primary model: gemini-2.5-flash
    """

    DEFAULT_MODEL = "gemini-2.5-flash"
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
        Initialize the Gemini client.
        """
        if config is not None:
            self.config = config
            self.api_key = getattr(config, "api_key", None) or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
            self.model = getattr(config, "model", None) or self.DEFAULT_MODEL
        else:
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
            self.model = model or os.environ.get("GEMINI_LLM_MODEL") or os.environ.get("LLM_MODEL") or self.DEFAULT_MODEL
            from ..config.llm_config import GeminiConfig
            self.config = GeminiConfig(api_key=self.api_key, model=self.model)

        self.review_id = review_id if review_id and review_id != "default" else f"session_{uuid.uuid4().hex[:8]}"
        self.api_url = api_url or os.environ.get("GEMINI_API_BASE_URL")
        self.telemetry = telemetry or LLMTelemetryManager()
        self.retry_engine = RetryEngine()
        self.tracker: ReviewLLMTracker = get_review_tracker(self.review_id)
        self.cache: LLMStructuredCache = get_llm_cache()

        self._client = None
        if genai is not None and self.api_key and self.api_key not in ("mock_key", "your_gemini_api_key_here"):
            http_options = None
            if self.api_url and "googleapis.com" not in self.api_url:
                http_options = types.HttpOptions(base_url=self.api_url) if types else None
            try:
                self._client = genai.Client(
                    api_key=self.api_key,
                    http_options=http_options,
                )
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")

        logger.info(f"Gemini LLM initialized with model {self.model}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai is not installed. Please install it using 'pip install google-genai'.")
            effective_key = self.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY", "")
            if not effective_key or effective_key in ("mock_key", "your_gemini_api_key_here"):
                raise ValueError("Gemini API key is required when Gemini LLM functionality is enabled.")
            self._client = genai.Client(api_key=effective_key)
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
        Generate a structured code review using the Gemini API.
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

        is_real_test = os.environ.get("GEMINI_REAL_TEST", "").lower() == "true"

        # Check response cache (bypassed in real test mode)
        if not is_real_test:
            cached = self.cache.get(system_instruction, user_content, target_model)
            if cached is not None:
                logger.debug(f"GeminiClient cache hit for review {self.review_id}")
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
        if is_real_test:
            candidate_models = [target_model]
        else:
            fallback_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]
            candidate_models = self.tracker.get_available_models(target_model, fallback_models)

        if not candidate_models:
            if is_real_test:
                raise RuntimeError("All configured Gemini models exhausted in real test mode.")
            logger.warning(f"All configured Gemini models exhausted for review {self.review_id}; returning degraded review.")
            self.tracker.set_degraded_mode("all_models_exhausted")
            return self._build_degraded_review("All Gemini models exhausted; review generated from deterministic findings.")

        gen_config = None
        if types is not None:
            config_kwargs = {
                "response_mime_type": "application/json",
                "system_instruction": system_instruction,
            }
            if hasattr(types, "AutomaticFunctionCallingConfig"):
                config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
            gen_config = types.GenerateContentConfig(**config_kwargs)

        max_transient_retries = 1 if is_real_test else 2

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
                    cleaned_content = self._clean_json_text(content)
                    parsed_json = json.loads(cleaned_content)
                    if not isinstance(parsed_json, dict):
                        parsed_json = {"review_summary": str(parsed_json)}

                    parsed_json = self._normalize_review_payload(parsed_json)
                    self.tracker.record_request()
                    if not is_real_test:
                        self.cache.set(system_instruction, user_content, current_model, parsed_json)

                    return ReviewResponse.model_validate(parsed_json)

                except json.JSONDecodeError as jde:
                    if is_real_test:
                        raise RuntimeError(f"JSON decode error with model {current_model} in real test mode: {jde}") from jde
                    logger.error(f"JSON Decode Error on attempt {attempt} with model {current_model}: {jde}")
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

                    if is_daily_quota:
                        self.tracker.mark_model_exhausted(current_model, "daily_quota_exhausted")
                        logger.warning(
                            f"Gemini daily quota exhausted for model {current_model}; skipping model for remainder of review {self.review_id}."
                        )
                        break

                    if is_rpm_rate_limit:
                        if attempt < max_transient_retries:
                            sleep_time = min(3.0, 1.5 * (1.5 ** attempt) + random.uniform(0.1, 0.4))
                            logger.info(
                                f"Temporary Gemini rate limit for {current_model} on review {self.review_id}; retrying in {sleep_time:.1f}s."
                            )
                            time.sleep(sleep_time)
                            continue
                        else:
                            self.tracker.mark_model_rate_limited(current_model, cooldown_seconds=30.0)
                            logger.warning(
                                f"Temporary rate limit exceeded on {current_model}; switching to next fallback model."
                            )
                            break

                    if is_server_error:
                        if attempt < max_transient_retries:
                            time.sleep(1.5)
                            continue
                        else:
                            break

                    logger.error(f"Gemini error with {current_model}: {e}")
                    break

        self.tracker.set_degraded_mode("all_models_failed")
        return self._build_degraded_review("Gemini generation unavailable; review generated from deterministic findings.")

    def _normalize_review_payload(self, parsed_json: dict) -> dict:
        """Normalize required review schema fields."""
        if "review_summary" not in parsed_json:
            parsed_json["review_summary"] = parsed_json.get("summary", parsed_json.get("description", "Code review completed."))
        if "overall_severity" not in parsed_json:
            parsed_json["overall_severity"] = parsed_json.get("severity", "medium")
        if "findings" not in parsed_json:
            raw_findings = parsed_json.get("issues", parsed_json.get("vulnerabilities", []))
            if isinstance(raw_findings, list):
                parsed_json["findings"] = raw_findings
            elif "finding" in parsed_json and isinstance(parsed_json["finding"], dict):
                parsed_json["findings"] = [parsed_json["finding"]]
            else:
                parsed_json["findings"] = []

        # Normalize findings references & code_suggestions
        if isinstance(parsed_json.get("findings"), list):
            for finding in parsed_json["findings"]:
                if isinstance(finding, dict):
                    if "references" in finding and isinstance(finding["references"], list):
                        finding["references"] = [
                            (r.get("url") or r.get("name") or str(r)) if isinstance(r, dict) else str(r)
                            for r in finding["references"]
                        ]
                    if "code_suggestion" in finding and isinstance(finding["code_suggestion"], (dict, list)):
                        finding["code_suggestion"] = json.dumps(finding["code_suggestion"])

        if "evidence_summary" not in parsed_json:
            parsed_json["evidence_summary"] = parsed_json.get("evidence", "")
        if "reasoning_trace" not in parsed_json:
            parsed_json["reasoning_trace"] = parsed_json.get("reasoning", "")
        if "confidence" not in parsed_json:
            parsed_json["confidence"] = 0.90
        if "priority" not in parsed_json:
            parsed_json["priority"] = parsed_json.get("severity", "medium")
        if "remediation_summary" not in parsed_json:
            parsed_json["remediation_summary"] = parsed_json.get("remediation", parsed_json.get("fix", ""))

        # Normalize global references & code_suggestions to list[str]
        if "references" in parsed_json and isinstance(parsed_json["references"], list):
            parsed_json["references"] = [
                (r.get("url") or r.get("name") or str(r)) if isinstance(r, dict) else str(r)
                for r in parsed_json["references"]
            ]
        if "code_suggestions" in parsed_json and isinstance(parsed_json["code_suggestions"], list):
            parsed_json["code_suggestions"] = [
                (s.get("code") or s.get("suggestion") or str(s)) if isinstance(s, dict) else str(s)
                for s in parsed_json["code_suggestions"]
            ]
        return parsed_json

    def _build_degraded_review(self, message: str) -> ReviewResponse:
        """Construct a valid fallback ReviewResponse when LLM generation is unavailable."""
        return ReviewResponse(
            review_summary=message,
            overall_severity="low",
            findings=[],
            evidence_summary="Deterministic analysis completed.",
            reasoning_trace=message,
            confidence=0.5,
            priority="low",
            remediation_summary="",
            code_suggestions=[],
            references=[],
            review_metadata={"llm_status": "degraded"},
        )

    def _clean_json_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def generate_raw(self, prompt_text: str, system_instruction: str = "") -> str:
        """
        Generate raw text response with Gemini.
        """
        gen_config = None
        if types is not None and system_instruction:
            gen_config = types.GenerateContentConfig(system_instruction=system_instruction)

        def _call_gemini_raw():
            client = self._get_client()
            return client.models.generate_content(
                model=self.model,
                contents=prompt_text,
                config=gen_config,
            )

        response = self.retry_engine.execute_with_retry(
            _call_gemini_raw,
            max_retries=getattr(self.config, "max_retries", 2),
            retry_delay=getattr(self.config, "retry_delay", 1.0),
        )

        return response.text if hasattr(response, "text") else str(response)
