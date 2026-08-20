"""
Google Gemini API client implementation.
"""
import os
import json
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

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """
    Client for Google Gemini API using the official Google GenAI SDK.
    Primary model: gemini-3.6-flash
    """

    DEFAULT_MODEL = "gemini-3.6-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        config: Any = None,
        telemetry: Optional[LLMTelemetryManager] = None,
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

        self.api_url = api_url or os.environ.get("GEMINI_API_BASE_URL")
        self.telemetry = telemetry or LLMTelemetryManager()
        self.retry_engine = RetryEngine()

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

    def generate_review(self, prompt: Any, config: Any = None) -> ReviewResponse:
        """
        Generate a structured review response using JSON mode with Gemini 3.6 Flash.
        Deprecated sampling parameters (temperature, top_p, top_k) are omitted.
        """
        model = config.get("model", self.model) if isinstance(config, dict) else (getattr(config, "model", None) or self.model)

        # Handle prompt extraction
        system_instruction = ""
        user_content = ""
        if hasattr(prompt, "system_instruction") and hasattr(prompt, "user_prompt"):
            system_instruction = prompt.system_instruction
            user_content = prompt.user_prompt
        elif isinstance(prompt, list):
            for m in prompt:
                if isinstance(m, dict) and m.get("role") == "system":
                    system_instruction = m.get("content", "")
                elif isinstance(m, dict) and m.get("role") == "user":
                    user_content = m.get("content", "")
        elif isinstance(prompt, dict):
            system_instruction = prompt.get("system_instruction", "")
            user_content = prompt.get("user_prompt", prompt.get("prompt", str(prompt)))
        else:
            user_content = str(prompt)

        if not system_instruction:
            system_instruction = (
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

        gen_config = None
        if types is not None:
            config_kwargs = {
                "response_mime_type": "application/json",
                "system_instruction": system_instruction,
            }
            gen_config = types.GenerateContentConfig(**config_kwargs)

        def _call_gemini():
            client = self._get_client()
            try:
                return client.models.generate_content(
                    model=model,
                    contents=user_content,
                    config=gen_config,
                )
            except Exception as e:
                err_str = str(e).lower()
                if "generaterequestsperday" in err_str:
                    for fb in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]:
                        if fb != model:
                            logger.info(f"Switching to fallback model {fb} due to daily quota limit on {model}.")
                            return client.models.generate_content(
                                model=fb,
                                contents=user_content,
                                config=gen_config,
                            )
                raise

        response = self.retry_engine.execute_with_retry(
            _call_gemini,
            max_retries=getattr(self.config, "max_retries", 3),
            retry_delay=getattr(self.config, "retry_delay", 1.0),
        )

        content = response.text if hasattr(response, "text") else str(response)

        # Parse JSON content
        cleaned_content = content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()

        parsed_json = json.loads(cleaned_content)
        if not isinstance(parsed_json, dict):
            parsed_json = {"review_summary": str(parsed_json)}

        # Normalize required fields
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

        return ReviewResponse.model_validate(parsed_json)

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
            max_retries=getattr(self.config, "max_retries", 3),
            retry_delay=getattr(self.config, "retry_delay", 1.0),
        )

        return response.text if hasattr(response, "text") else str(response)
