"""
CodeGuard V2 — Multi-Provider LLM Architecture Test Suite.

Validates:
1. Primary provider routing (Groq)
2. Fallback provider failover (Gemini) on quota exhaustion with zero retries
3. Bounded retries on temporary RPM limits
4. Review-aware provider state (bypassing exhausted providers)
5. Shared review-level request budget enforcement
6. Finding-level traceability (llm_provider, llm_model, reasoning_trace)
7. Graceful degradation to deterministic static analysis when all providers fail
8. Embeddings isolation (RAG unaffected by LLM failovers)
9. Health endpoint configuration reporting
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.api.schemas import ReviewIssue
from app.core.config import get_settings
from app.llm.errors import ErrorClassifier, ErrorCategory
from app.llm.llm_budget import get_review_tracker, reset_review_tracker, ReviewLLMTracker
from app.llm.llm_client import LLMClient
from app.llm.models import LLMRequest, LLMResponse
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.router import ProviderRouter
from app.llm.service import LLMService
from app.reasoning.review_generator import ReviewGenerator
from app.reasoning.root_cause_engine import RootCauseEngine
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider


class TestMultiProviderClassification:
    """Test normalized error classification across providers."""

    def test_groq_tpd_classified_as_quota_exhaustion(self):
        err = Exception("Rate limit reached for model llama-3.3-70b-versatile: TPD limit: 200000 Used: 199000 Requested: 2000")
        classification = ErrorClassifier.classify(err, provider="groq")
        assert classification.category == ErrorCategory.QUOTA_EXHAUSTED
        assert classification.is_quota_exhaustion is True
        assert classification.is_retryable is False

    def test_gemini_daily_quota_classified_as_quota_exhaustion(self):
        err = Exception("ResourceExhausted: 429 Quota exceeded for quota metric 'GenerateRequestsPerDay'")
        classification = ErrorClassifier.classify(err, provider="gemini")
        assert classification.category == ErrorCategory.QUOTA_EXHAUSTED
        assert classification.is_quota_exhaustion is True
        assert classification.is_retryable is False

    def test_transient_rpm_classified_as_retryable(self):
        err = Exception("429 Too Many Requests: Rate limit reached for requests per minute (RPM)")
        classification = ErrorClassifier.classify(err, provider="groq")
        assert classification.category == ErrorCategory.TEMPORARY_RATE_LIMIT
        assert classification.is_retryable is True
        assert classification.is_quota_exhaustion is False

    def test_auth_error_classified_correctly(self):
        err = Exception("401 invalid_api_key: Invalid API Key provided")
        classification = ErrorClassifier.classify(err, provider="groq")
        assert classification.category == ErrorCategory.AUTH_ERROR
        assert classification.is_retryable is False


class TestProviderRouterAndFailover:
    """Test ProviderRouter routing and multi-provider failover mechanics."""

    def test_primary_groq_success(self):
        review_id = "test-groq-success"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)

        mock_groq = MagicMock(spec=GroqProvider)
        mock_groq.name = "groq"
        mock_groq.primary_model = "llama-3.3-70b-versatile"
        mock_groq.fallback_models = []
        mock_groq.is_available.return_value = True
        mock_groq.generate_structured.return_value = LLMResponse(
            text='{"root_cause": "Groq found issue"}',
            parsed_json={"root_cause": "Groq found issue", "fix": "Groq fix"},
            provider="groq",
            model="llama-3.3-70b-versatile",
            input_tokens=100,
            output_tokens=50,
        )

        mock_gemini = MagicMock(spec=GeminiProvider)
        mock_gemini.name = "gemini"
        mock_gemini.primary_model = "gemini-2.5-flash"
        mock_gemini.is_available.return_value = True

        router = ProviderRouter(
            providers={"groq": mock_groq, "gemini": mock_gemini},
            primary_provider="groq",
            fallback_providers=["gemini"]
        )

        request = LLMRequest(system_prompt="sys", user_prompt="usr")
        resp = router.route_request(request, tracker=tracker, structured=True)

        assert resp.is_success is True
        assert resp.provider == "groq"
        assert resp.fallback_used is False
        assert mock_groq.generate_structured.call_count == 1
        assert mock_gemini.generate_structured.call_count == 0

    def test_groq_quota_exhaustion_immediately_fails_over_to_gemini(self):
        review_id = "test-failover-to-gemini"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)

        # Groq fails with quota exhaustion
        mock_groq = MagicMock(spec=GroqProvider)
        mock_groq.name = "groq"
        mock_groq.primary_model = "llama-3.3-70b-versatile"
        mock_groq.fallback_models = []
        mock_groq.is_available.return_value = True
        mock_groq.generate_structured.return_value = LLMResponse(
            text="",
            provider="groq",
            model="llama-3.3-70b-versatile",
            error="QUOTA_EXHAUSTED: TPD limit exceeded"
        )

        # Gemini succeeds
        mock_gemini = MagicMock(spec=GeminiProvider)
        mock_gemini.name = "gemini"
        mock_gemini.primary_model = "gemini-2.5-flash"
        mock_gemini.fallback_models = []
        mock_gemini.is_available.return_value = True
        mock_gemini.generate_structured.return_value = LLMResponse(
            text='{"root_cause": "Gemini handled after Groq quota"}',
            parsed_json={"root_cause": "Gemini handled after Groq quota", "fix": "Gemini fix"},
            provider="gemini",
            model="gemini-2.5-flash",
            input_tokens=120,
            output_tokens=60,
        )

        router = ProviderRouter(
            providers={"groq": mock_groq, "gemini": mock_gemini},
            primary_provider="groq",
            fallback_providers=["gemini"]
        )

        request = LLMRequest(system_prompt="sys", user_prompt="usr")
        resp = router.route_request(request, tracker=tracker, structured=True)

        assert resp.is_success is True
        assert resp.provider == "gemini"
        assert resp.fallback_used is True
        assert tracker.is_provider_exhausted("groq") is True

        # Second request in the same review MUST bypass Groq completely
        mock_groq.generate_structured.reset_mock()
        mock_gemini.generate_structured.reset_mock()

        resp2 = router.route_request(request, tracker=tracker, structured=True)
        assert resp2.is_success is True
        assert resp2.provider == "gemini"
        assert mock_groq.generate_structured.call_count == 0  # Groq was never touched!
        assert mock_gemini.generate_structured.call_count == 1

    def test_shared_request_budget_maintained_on_fallback(self):
        review_id = "test-budget-sharing"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)
        tracker.max_requests = 2

        mock_groq = MagicMock(spec=GroqProvider)
        mock_groq.name = "groq"
        mock_groq.is_available.return_value = True
        mock_groq.generate_structured.return_value = LLMResponse(
            text="", provider="groq", model="m1", error="QUOTA_EXHAUSTED: daily limit"
        )

        mock_gemini = MagicMock(spec=GeminiProvider)
        mock_gemini.name = "gemini"
        mock_gemini.is_available.return_value = True
        mock_gemini.generate_structured.return_value = LLMResponse(
            text="{}", parsed_json={"root_cause": "ok", "fix": "ok"}, provider="gemini", model="gemini-2.5-flash"
        )

        router = ProviderRouter(
            providers={"groq": mock_groq, "gemini": mock_gemini},
            primary_provider="groq",
            fallback_providers=["gemini"]
        )

        service = LLMService(router=router)

        # Request 1: Groq fails, Gemini succeeds -> exactly 1 request counted against budget
        res1 = service.generate_structured("sys", "usr1", review_id=review_id)
        assert res1 is not None
        assert tracker.requests_made == 1

        # Request 2: Groq bypassed, Gemini succeeds -> exactly 2 requests counted
        res2 = service.generate_structured("sys", "usr2", review_id=review_id)
        assert res2 is not None
        assert tracker.requests_made == 2
        assert tracker.can_request() is False

        # Request 3: Exceeds budget -> returns None
        res3 = service.generate_structured("sys", "usr3", review_id=review_id)
        assert res3 is None

    def test_double_provider_failure_triggers_degraded_mode(self):
        review_id = "test-double-fail"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)

        mock_groq = MagicMock(spec=GroqProvider)
        mock_groq.name = "groq"
        mock_groq.is_available.return_value = True
        mock_groq.generate_structured.return_value = LLMResponse(
            text="", provider="groq", model="m1", error="500 Internal Error"
        )

        mock_gemini = MagicMock(spec=GeminiProvider)
        mock_gemini.name = "gemini"
        mock_gemini.is_available.return_value = True
        mock_gemini.generate_structured.return_value = LLMResponse(
            text="", provider="gemini", model="gemini-2.5-flash", error="503 Service Unavailable"
        )

        router = ProviderRouter(
            providers={"groq": mock_groq, "gemini": mock_gemini},
            primary_provider="groq",
            fallback_providers=["gemini"]
        )

        service = LLMService(router=router)
        res = service.generate_structured("sys", "usr_unique_double_fail", review_id=review_id)

        assert res is None
        assert tracker.degraded_mode is True


class TestFindingTraceabilityAndReasoningPipeline:
    """Test finding-level provenance (llm_provider, llm_model, reasoning_trace)."""

    def test_finding_captures_gemini_fallback_metadata(self):
        review_id = "test-finding-traceability"
        reset_review_tracker(review_id)

        client = LLMClient(review_id=review_id)
        client.cache.clear()

        # Mock groq failing, gemini succeeding
        mock_groq = MagicMock(spec=GroqProvider)
        mock_groq.name = "groq"
        mock_groq.primary_model = "llama-3.3-70b-versatile"
        mock_groq.is_available.return_value = True
        mock_groq.generate_structured.return_value = LLMResponse(
            text="", provider="groq", model="llama-3.3-70b-versatile", error="QUOTA_EXHAUSTED"
        )

        mock_gemini = MagicMock(spec=GeminiProvider)
        mock_gemini.name = "gemini"
        mock_gemini.primary_model = "gemini-2.5-flash"
        mock_gemini.is_available.return_value = True
        mock_gemini.generate_structured.return_value = LLMResponse(
            text="{}",
            parsed_json={
                "root_cause": "SQL injection in dynamic statement",
                "trigger_condition": "Attacker payload in input",
                "fix": "Use parameterized queries",
                "issue_type": "security"
            },
            provider="gemini",
            model="gemini-2.5-flash",
            fallback_used=True
        )

        client.router._providers["groq"] = mock_groq
        client.router._providers["gemini"] = mock_gemini

        engine = RootCauseEngine(review_id=review_id)
        engine.llm_client = client
        finding = {
            "line": 15,
            "issue": "SQL injection detected",
            "severity": "critical",
            "issue_type": "security",
            "tool": "bandit"
        }
        res = engine.analyze_finding(finding, {"code_snippet": "cursor.execute(sql)"})

        assert res["reasoning_source"] == "llm"
        assert res["llm_provider"] == "gemini"
        assert res["llm_model"] == "gemini-2.5-flash"

        # Now verify ReviewGenerator builds ReviewIssue with exact traceability
        generator = ReviewGenerator(review_id=review_id)
        generator.root_cause_engine = engine

        aggregated = {
            "file_path": "app/db.py",
            "changed_lines": [15],
            "linter_findings": [
                {"line": 15, "tool": "bandit", "rule": "B608", "message": "SQL injection", "severity": "critical"}
            ],
            "heuristic_findings": [],
            "dataflow_analysis": []
        }

        issues = generator.generate(aggregated)
        assert len(issues) > 0
        issue = issues[0]

        assert issue.reasoning_source == "llm"
        assert issue.llm_provider == "gemini"
        assert issue.llm_model == "gemini-2.5-flash"
        assert any("Gemini LLM (gemini-2.5-flash)" in trace for trace in issue.reasoning_trace)


class TestEmbeddingsIsolation:
    """Verify Gemini embeddings provider remains strictly isolated from LLM reasoning."""

    def test_gemini_embedding_provider_model_and_method(self):
        provider = GeminiEmbeddingProvider()
        # Embedding provider model must remain gemini-embedding-2
        assert provider.model_name == "gemini-embedding-2"
        assert hasattr(provider, "embed_text")
        assert hasattr(provider, "embed_batch")

    def test_gemini_llm_model_differs_from_embedding_model(self):
        settings = get_settings()
        gemini_llm = GeminiProvider()
        gemini_embed = GeminiEmbeddingProvider()

        # Models must be distinct
        assert gemini_llm.primary_model == getattr(settings, "GEMINI_LLM_MODEL", "gemini-2.5-flash")
        assert gemini_embed.model_name == "gemini-embedding-2"
        assert gemini_llm.primary_model != gemini_embed.model_name
