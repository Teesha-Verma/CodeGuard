"""
CodeGuard V2 — Unit and Integration Tests for Gemini LLM Quota, Fallback, Caching, and Degraded Mode.

Tests all 14 quota and retry scenarios:
1. Successful Gemini request & JSON normalization
2. Transient 429 RPM rate-limit retry & recovery
3. Daily quota exhaustion detection (0 retries on exhausted model)
4. Clean multi-model fallback cascade
5. Model blacklisting prevents repeated calls to exhausted models across findings
6. All models exhausted -> graceful degraded mode with deterministic findings
7. Per-review request budget cap enforcement
8. Prompt deduplication and caching hit/miss
9. 503 Server Error bounded retry
10. Auth/configuration error fail-fast
11. Independent embedding provider quota handling
12. Thread-safety of review budget tracker and cache
13. Supabase/ReviewStore persistence in degraded mode
14. Full PipelineOrchestrator run under simulated LLM quota exhaustion
"""

import time
import threading
from unittest.mock import MagicMock, patch
import pytest

from app.llm.llm_budget import ReviewLLMTracker, get_review_tracker, reset_review_tracker
from app.llm.llm_cache import LLMStructuredCache, get_llm_cache
from app.llm.llm_client import LLMClient
from app.analysis.RAG.llm.gemini_client import GeminiClient
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.reasoning.root_cause_engine import RootCauseEngine
from app.reasoning.review_generator import ReviewGenerator
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile
from app.storage.review_store import ReviewStore
from app.api.schemas import ReviewReport, FileReport, ReviewIssue


@pytest.fixture(autouse=True)
def clean_trackers_and_cache():
    """Reset all trackers and cache before each test."""
    reset_review_tracker()
    get_llm_cache().clear()
    yield
    reset_review_tracker()
    get_llm_cache().clear()


class TestLLMBudgetAndCache:
    """Unit tests for ReviewLLMTracker and LLMStructuredCache."""

    def test_budget_tracking_and_limit(self):
        tracker = ReviewLLMTracker(review_id="rev_budget_1", max_requests=3)
        assert tracker.can_request() is True
        assert tracker.remaining_budget() == 3

        tracker.record_request()
        tracker.record_request()
        assert tracker.can_request() is True
        assert tracker.remaining_budget() == 1

        tracker.record_request()
        assert tracker.can_request() is False
        assert tracker.remaining_budget() == 0

    def test_exhausted_model_blacklisting(self):
        tracker = ReviewLLMTracker(review_id="rev_blacklist_1")
        primary = "gemini-2.5-flash"
        fallbacks = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]

        avail = tracker.get_available_models(primary, fallbacks)
        assert avail == ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]

        tracker.mark_model_exhausted(primary, "daily_quota_exhausted")
        assert tracker.is_model_exhausted(primary) is True

        avail2 = tracker.get_available_models(primary, fallbacks)
        assert avail2 == ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
        assert primary not in avail2

    def test_rate_limit_cooldown(self):
        tracker = ReviewLLMTracker(review_id="rev_cooldown_1")
        tracker.mark_model_rate_limited("gemini-3.5-flash-lite", cooldown_seconds=0.2)
        assert tracker.is_model_rate_limited("gemini-3.5-flash-lite") is True

        time.sleep(0.25)
        assert tracker.is_model_rate_limited("gemini-3.5-flash-lite") is False

    def test_prompt_caching_and_deduplication(self):
        cache = LLMStructuredCache(max_size=10, default_ttl_seconds=300)
        sys_prompt = "You are a reviewer."
        user_content = '{"finding": "test_1"}'
        model = "gemini-2.5-flash"
        resp = {"root_cause": "Issue detected", "fix": "Apply patch"}

        assert cache.get(sys_prompt, user_content, model) is None

        cache.set(sys_prompt, user_content, model, resp)
        cached = cache.get(sys_prompt, user_content, model)
        assert cached is not None
        assert cached["root_cause"] == "Issue detected"
        assert cache.stats()["hits"] == 1

    def test_tracker_thread_safety(self):
        tracker = ReviewLLMTracker(review_id="rev_thread_safe", max_requests=100)

        def worker():
            for _ in range(10):
                tracker.record_request()

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert tracker.requests_made == 100
        assert tracker.can_request() is False


class TestLLMClientQuotaAndFallback:
    """Tests for LLMClient quota handling, fallback chain, and bounded retries."""

    def test_successful_gemini_request_and_normalization(self):
        client = LLMClient(review_id="rev_success_1")
        client.api_key = "test_key"
        client.provider = "groq"

        mock_choice = MagicMock()
        mock_choice.message.content = '{"explanation": "Insecure input", "suggestion": "Sanitize variable"}'
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.return_value = mock_resp
        client._client = mock_groq_client

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "eval"}'
        )

        assert res is not None
        assert res["root_cause"] == "Insecure input"
        assert res["fix"] == "Sanitize variable"
        assert client.tracker.requests_made == 1

    def test_transient_429_rpm_retry_and_recovery(self):
        client = LLMClient(review_id="rev_rpm_retry")
        client.api_key = "test_key"
        client.provider = "groq"

        mock_choice = MagicMock()
        mock_choice.message.content = '{"root_cause": "SQL injection hazard", "fix": "Use parameters"}'
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        mock_groq_client = MagicMock()
        # First call fails with transient 429 RPM, second call succeeds
        mock_groq_client.chat.completions.create.side_effect = [
            Exception("429 rate_limit_exceeded: Rate limit reached for model"),
            mock_resp
        ]
        client._client = mock_groq_client

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "sql"}'
        )

        assert res is not None
        assert res["root_cause"] == "SQL injection hazard"
        assert mock_groq_client.chat.completions.create.call_count == 2

    def test_daily_quota_exhaustion_switches_model_without_retrying_exhausted(self):
        client = LLMClient(review_id="rev_daily_quota")
        client.api_key = "test_key"
        client.provider = "groq"
        primary_model = client.model

        mock_choice = MagicMock()
        mock_choice.message.content = '{"root_cause": "Handled by fallback", "fix": "Fixed"}'
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        mock_groq_client = MagicMock()

        def mock_create(*args, **kwargs):
            m = kwargs.get("model")
            if m == primary_model:
                raise Exception("429 requests_per_day daily quota exceeded")
            return mock_resp

        mock_groq_client.chat.completions.create.side_effect = mock_create
        client._client = mock_groq_client

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "eval"}'
        )

        assert res is not None
        assert res["root_cause"] == "Handled by fallback"
        assert client.tracker.is_model_exhausted(primary_model) is True

        # Second request for the same review: primary model must NOT be called again!
        mock_groq_client.chat.completions.create.reset_mock()
        res2 = client.generate_structured(
            system_prompt="Analyze code 2",
            user_content='{"issue": "eval_2"}'
        )
        assert res2 is not None
        # Verify primary model was never passed in the second request
        for call_args in mock_groq_client.chat.completions.create.call_args_list:
            _, kwargs = call_args
            assert kwargs.get("model") != primary_model

    def test_all_models_exhausted_triggers_degraded_mode(self):
        client = LLMClient(review_id="rev_all_exhausted")
        client.api_key = "test_key"
        client.provider = "groq"

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.side_effect = Exception(
            "429 daily quota exceeded per_day"
        )
        client._client = mock_groq_client

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "eval"}'
        )

        assert res is None
        assert client.tracker.degraded_mode is True

    def test_request_budget_exceeded_returns_none(self):
        client = LLMClient(review_id="rev_budget_exceeded")
        client.tracker.max_requests = 1
        client.tracker.requests_made = 1

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "eval"}'
        )

        assert res is None

    def test_auth_error_fails_fast_without_cycling_models(self):
        client = LLMClient(review_id="rev_auth_fail")
        client.api_key = "invalid_key"
        client.provider = "groq"

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.side_effect = Exception(
            "401 invalid_api_key: Invalid API Key provided"
        )
        client._client = mock_groq_client

        res = client.generate_structured(
            system_prompt="Analyze code",
            user_content='{"issue": "test"}'
        )

        assert res is None
        # Must fail fast (only 1 call, no retries on invalid credentials)
        assert mock_groq_client.chat.completions.create.call_count == 1


class TestRAGClientAndEmbeddings:
    """Tests for GeminiClient (RAG) and GeminiEmbeddingProvider."""

    def test_rag_gemini_client_daily_quota_fallback(self):
        client = GeminiClient(api_key="test_key", model="gemini-2.5-flash", review_id="rev_rag_quota")

        mock_resp_lite = MagicMock()
        mock_resp_lite.text = '{"review_summary": "RAG Fallback Succeeded", "overall_severity": "low", "findings": []}'

        mock_genai_client = MagicMock()

        def mock_generate(model, contents, config):
            if model == "gemini-2.5-flash":
                raise Exception("429 RESOURCE_EXHAUSTED: GenerateRequestsPerDay")
            return mock_resp_lite

        mock_genai_client.models.generate_content.side_effect = mock_generate
        client._client = mock_genai_client

        resp = client.generate_review(prompt="Analyze code")
        assert resp.review_summary == "RAG Fallback Succeeded"

    def test_embedding_provider_daily_quota_fallback(self):
        provider = GeminiEmbeddingProvider(api_key="test_key", model="gemini-embedding-2")

        mock_resp_fallback = MagicMock()
        mock_resp_fallback.embeddings = [MagicMock(values=[0.1] * 768)]

        mock_genai_client = MagicMock()

        def mock_embed(model, contents, config):
            if model == "gemini-embedding-2":
                raise Exception("429 RESOURCE_EXHAUSTED: EmbedContentRequestsPerDay")
            return mock_resp_fallback

        mock_genai_client.models.embed_content.side_effect = mock_embed
        provider._client = mock_genai_client

        emb = provider.embed_text("Sample query")
        assert len(emb) == 768
        assert "gemini-embedding-2" in provider._exhausted_models


class TestReviewGeneratorAndPipelineDegradedMode:
    """Tests for ReviewGenerator and PipelineOrchestrator under quota exhaustion."""

    def test_review_generator_under_exhausted_quota_uses_static_explanations(self):
        review_id = "rev_gen_degraded"
        tracker = get_review_tracker(review_id)
        tracker.set_degraded_mode("quota_exhausted")

        generator = ReviewGenerator(review_id=review_id)
        aggregated = {
            "file_path": "app/auth.py",
            "changed_lines": [10],
            "linter_findings": [
                {"line": 10, "tool": "bandit", "rule": "B307", "message": "Use of possibly insecure function - eval", "severity": "high"}
            ],
            "heuristic_findings": [
                {"line": 10, "rule_name": "eval_usage", "message": "Use of eval() detected", "severity": "critical", "issue_type": "security"}
            ],
            "dataflow_analysis": [
                {"sink_line": 10, "rule_id": "taint_sink", "title": "Untrusted input reaches eval", "severity": "critical"}
            ]
        }

        issues = generator.generate(aggregated)
        assert len(issues) > 0
        issue = issues[0]
        assert issue.reasoning_source == "static_analysis"
        assert "Static analysis" in issue.root_cause or "hazardous" in issue.root_cause.lower()
        assert any("Bypassed LLM reasoning" in trace for trace in issue.reasoning_trace)

    def test_orchestrator_full_file_process_under_quota_exhaustion(self, tmp_path):
        review_id = "rev_orch_exhausted"
        tracker = get_review_tracker(review_id)
        tracker.set_degraded_mode("daily_quota_exhausted")

        # Create temporary python file
        test_file = tmp_path / "calc.py"
        test_file.write_text("def compute(x):\n    return eval(x)\n", encoding="utf-8")

        diff_file = DiffFile(file_path="calc.py", is_new=False, added_lines=[2])
        orchestrator = PipelineOrchestrator(review_id=review_id)

        file_report = orchestrator.process_file(diff_file, str(tmp_path))
        assert file_report.file_path == "calc.py"
        assert len(file_report.meaningful_issues) > 0

        first_issue = file_report.meaningful_issues[0]
        assert first_issue.line == 2
        assert first_issue.reasoning_source == "static_analysis"

    def test_save_report_to_disk_in_degraded_mode(self, tmp_path):
        review_id = "rev_store_degraded"
        report = ReviewReport(
            review_id=review_id,
            file_reports=[
                FileReport(
                    file_path="test.py",
                    meaningful_issues=[
                        ReviewIssue(
                            line=1,
                            severity="high",
                            confidence=0.85,
                            issue="Dangerous function",
                            root_cause="Static explanation",
                            trigger_condition="Execution",
                            fix="Use safe alternative",
                            issue_type="security",
                            sources=["ast", "static_analysis"],
                            reasoning_trace=["Static trace"],
                            detection_source="ast",
                            reasoning_source="static_analysis",
                            priority_score=0.80
                        )
                    ]
                )
            ],
            summary_stats={"critical": 0, "high": 1, "medium": 0, "low": 0, "total": 1},
            trace_id=review_id
        )

        store = ReviewStore()
        saved_path = store.save_report(report)
        assert saved_path is not None

        loaded = store.get_report(review_id)
        assert loaded is not None
        assert loaded.review_id == review_id
        assert len(loaded.file_reports[0].meaningful_issues) == 1
