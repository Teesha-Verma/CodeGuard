"""Unit tests for Phase 4: Gemini LLM Integration Layer in app.analysis.RAG."""

import os
import pytest
from unittest.mock import MagicMock, patch

from app.analysis.RAG.config.llm_config import LLMConfig, GeminiConfig
from app.analysis.RAG.responses.review_schema import ReviewFinding, ReviewResponse, TypedReviewObject
from app.analysis.RAG.validation.response_validator import ResponseValidator, ResponseValidationResult
from app.analysis.RAG.retry.retry_engine import RetryEngine
from app.analysis.RAG.llm.base_client import BaseLLMClient
from app.analysis.RAG.llm.mock_client import MockGeminiClient
from app.analysis.RAG.llm.gemini_client import GeminiClient
from app.analysis.RAG.telemetry.llm_telemetry import LLMTelemetryManager, LLMUsageMetrics
from app.analysis.RAG.cache.llm_response_cache import LLMResponseCache


class TestReviewSchemaAndConfig:
    """Test response models and LLM configuration."""

    def test_review_response_schema(self):
        finding = ReviewFinding(
            title="SQL Injection Vulnerability",
            severity="critical",
            file_path="app/api/users.py",
            line_number=42,
            evidence="cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            reasoning="User input is directly concatenated into SQL query without parameterization.",
            priority="high",
            remediation="Use parameterized queries with placeholders.",
            code_suggestion="cursor.execute('SELECT * FROM users WHERE id=%s', (user_id,))",
            references=["OWASP-A03", "CWE-89"],
        )
        response = ReviewResponse(
            review_summary="Found 1 critical security vulnerability.",
            overall_severity="critical",
            findings=[finding],
            evidence_summary="Unsanitized user input concatenated into raw SQL query.",
            reasoning_trace="Taint flow traced from request params to raw execute call.",
            confidence=0.95,
            priority="high",
            remediation_summary="Parameterize all database queries.",
            code_suggestions=["cursor.execute('SELECT * FROM users WHERE id=%s', (user_id,))"],
            references=["OWASP-A03"],
        )
        assert response.overall_severity == "critical"
        assert len(response.findings) == 1
        assert response.confidence == 0.95

    def test_groq_config_defaults_and_env(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test_groq_key_123")
        monkeypatch.setenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
        config = LLMConfig.from_env()
        assert config.api_key == "test_groq_key_123"
        assert config.model == "llama-3.3-70b-versatile"
        assert config.json_mode is True


class TestResponseValidator:
    """Test structured output response validator."""

    def test_validate_json_string(self):
        validator = ResponseValidator()
        raw_json = '{"review_summary": "Clean code", "overall_severity": "low"}'
        is_valid, parsed, errs = validator.validate_json_string(raw_json)
        assert is_valid
        assert parsed["overall_severity"] == "low"

    def test_validate_markdown_json_block(self):
        validator = ResponseValidator()
        raw_markdown = """```json
{
  "review_summary": "Found issue",
  "overall_severity": "high"
}
```"""
        is_valid, parsed, errs = validator.validate_json_string(raw_markdown)
        assert is_valid
        assert parsed["overall_severity"] == "high"

    def test_validate_review_object_invalid_confidence(self):
        validator = ResponseValidator()
        invalid_review_dict = {
            "review_summary": "Summary",
            "overall_severity": "INVALID_SEVERITY",
            "confidence": 1.5,  # Out of range 0.0-1.0
        }
        res = validator.validate_review_object(invalid_review_dict)
        assert not res.is_valid
        assert len(res.errors) > 0


class TestRetryEngine:
    """Test retry engine with exponential backoff."""

    def test_retry_engine_success(self):
        retry_engine = RetryEngine()
        attempts = 0

        def flaky_call():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TimeoutError("Transient connection error")
            return "SUCCESS"

        res = retry_engine.execute_with_retry(flaky_call, max_retries=3, retry_delay=0.01)
        assert res == "SUCCESS"
        assert attempts == 2


class TestMockAndGeminiLLMClient:
    """Test BaseLLMClient implementations (Mock & Gemini)."""

    def test_mock_gemini_client(self):
        client = MockGeminiClient()
        assert "mock" in client.provider_name

        review = client.generate_review(prompt="Review user input handling")
        assert isinstance(review, (ReviewResponse, TypedReviewObject))
        assert review.confidence >= 0.8
        assert len(review.findings) > 0

    def test_gemini_client_initialization(self):
        config = GeminiConfig(api_key="mock_key", model="gemini-2.5-flash")
        client = GeminiClient(config=config)
        assert client.provider_name == "gemini"
        assert client.config.model == "gemini-2.5-flash"

    def test_gemini_client_generate_review_with_mocked_genai(self):
        config = GeminiConfig(api_key="test_api_key", model="gemini-2.5-flash")
        client = GeminiClient(config=config)

        mock_response = MagicMock()
        mock_response.text = '{"review_summary": "No critical issues", "overall_severity": "low", "findings": [], "evidence_summary": "", "reasoning_trace": "", "confidence": 0.95, "priority": "low", "remediation_summary": "", "code_suggestions": [], "references": [], "review_metadata": {}}'

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value = mock_response
        client._client = mock_genai_client

        review = client.generate_review(prompt="Analyze this code")
        assert isinstance(review, ReviewResponse)
        assert review.review_summary == "No critical issues"
        assert review.overall_severity == "low"

        # Verify no deprecated sampling params were passed
        mock_genai_client.models.generate_content.assert_called_once()
        _, kwargs = mock_genai_client.models.generate_content.call_args
        gen_config = kwargs.get("config")
        if gen_config is not None:
            assert not hasattr(gen_config, "temperature") or gen_config.temperature is None
            assert not hasattr(gen_config, "top_p") or gen_config.top_p is None
            assert not hasattr(gen_config, "top_k") or gen_config.top_k is None


class TestTelemetryAndResponseCache:
    """Test telemetry manager and response cache."""

    def test_telemetry_manager(self):
        telemetry = LLMTelemetryManager()
        metrics = LLMUsageMetrics(
            provider="gemini",
            prompt_tokens=150,
            completion_tokens=50,
            total_tokens=200,
            estimated_cost_usd=0.0001,
            latency_ms=320.0,
            request_size_bytes=600,
            response_size_bytes=200,
            model_name="gemini-2.5-flash",
            success=True,
            retry_count=0,
        )
        telemetry.record_request(metrics)
        stats = telemetry.get_summary_stats()
        assert stats["total_requests"] == 1
        assert stats["total_tokens"] == 200

        sanitized = telemetry.sanitize_prompt("Authorization: Bearer gsk_secret_12345 AIzaSyDummySecretKey1234567890abcdef")
        assert "gsk_secret_12345" not in sanitized
        assert "AIzaSyDummySecretKey1234567890abcdef" not in sanitized

    def test_llm_response_cache(self):
        cache = LLMResponseCache(max_size=2, ttl_seconds=60)
        review = ReviewResponse(
            review_summary="Cached review summary",
            overall_severity="low",
            findings=[],
            evidence_summary="",
            reasoning_trace="",
            confidence=0.9,
            priority="low",
            remediation_summary="",
            code_suggestions=[],
            references=[],
            review_metadata={},
        )
        cache.put(prompt_text="Analyze test code", model_name="gemini-2.5-flash", response=review)

        cached = cache.get(prompt_text="Analyze test code", model_name="gemini-2.5-flash")
        assert cached is not None
        assert cached.review_summary == "Cached review summary"
        assert cache.stats["hits"] == 1
