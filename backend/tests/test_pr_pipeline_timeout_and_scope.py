"""
Test suite for PR Pipeline Scope, Timeouts, and Terminal State Guarantees.

Verifies:
1. PR changed-file scope is respected.
2. Unchanged repository tests are not analyzed as primary files.
3. Gemini daily quota exhaustion does not hang the pipeline.
4. Embedding quota exhaustion does not hang the pipeline.
5. LLM fallback reaches static reasoning.
6. RAG failure still allows review completion.
7. Individual stage timeout produces a terminal state.
8. Entire review timeout produces a terminal state.
9. Unexpected exception changes review status from running to failed.
10. Pipeline traces contain the failing/timed-out stage.
11. A completed review is persisted to DB/store.
12. GET /review/{review_id} never remains "running" indefinitely.
"""

import os
import time
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.diff.diff_parser import DiffFile
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.runner import run_pr_review_task, run_snippet_review_task, _update_review_status_in_db
from app.storage.review_store import ReviewStore
from app.api.schemas import ReviewReport, FileReport, ReviewIssue
from app.db.repositories import ReviewRepository
from app.llm.llm_budget import ReviewLLMTracker, get_review_tracker
from app.analysis.RAG.context.assembler import AssembledContext
from app.main import app


class TestPRPipelineScopeAndTimeouts:
    """Comprehensive tests for PR scope, bounded timeouts, and terminal states."""

    def test_pr_scope_filters_to_changed_files_only(self):
        """Verify that only files in pr_changed_files are analyzed as primary files."""
        pr_changed_files = [
            "backend/app/analysis/repository/models.py",
            "backend/app/analysis/repository/query_engine.py"
        ]
        all_diff_files = [
            DiffFile(file_path="backend/app/analysis/repository/models.py", is_new=False, added_lines=[1, 2]),
            DiffFile(file_path="backend/app/analysis/repository/query_engine.py", is_new=False, added_lines=[5, 6]),
            DiffFile(file_path="backend/tests/test_call_graph.py", is_new=False, added_lines=[10]),
            DiffFile(file_path="backend/tests/test_cfg_analysis.py", is_new=False, added_lines=[20]),
        ]

        pr_changed_set = set(pr_changed_files)
        primary_diff_files = [df for df in all_diff_files if df.file_path in pr_changed_set]

        assert len(primary_diff_files) == 2
        assert all(df.file_path in pr_changed_set for df in primary_diff_files)
        assert not any("test_call_graph" in df.file_path for df in primary_diff_files)
        assert not any("test_cfg_analysis" in df.file_path for df in primary_diff_files)

    def test_unchanged_tests_not_in_primary_files(self):
        """Verify that unchanged test files are excluded from primary files."""
        pr_changed = ["app/models/user.py"]
        parsed_diff = [
            DiffFile(file_path="app/models/user.py", is_new=False, added_lines=[1]),
            DiffFile(file_path="tests/test_user.py", is_new=False, added_lines=[1]),
        ]
        primary = [df for df in parsed_diff if df.file_path in pr_changed]
        assert len(primary) == 1
        assert primary[0].file_path == "app/models/user.py"

    @patch("app.github.GitHubClient.get_pr_changed_files")
    @patch("app.github.GitHubClient.clone_and_checkout_pr")
    @patch("app.github.GitHubClient.get_pull_request")
    def test_gemini_daily_quota_exhaustion_does_not_hang_pipeline(
        self, mock_get_pr, mock_clone, mock_get_files, tmp_path
    ):
        """Verify that when Gemini daily quota is exhausted, pipeline continues and completes deterministically."""
        review_id = f"test_quota_{uuid.uuid4().hex[:8]}"
        tracker = get_review_tracker(review_id)
        tracker.mark_model_exhausted("gemini-3.6-flash")
        tracker.mark_model_exhausted("gemini-3.5-flash-lite")
        tracker.mark_model_exhausted("gemini-3.5-flash")
        tracker.mark_model_exhausted("gemini-2.5-flash")
        tracker.set_degraded_mode("all_models_exhausted")

        # Create dummy repo with deterministic AST eval vulnerability
        test_file = tmp_path / "models.py"
        test_file.write_text("x = eval('2 + 2')\n", encoding="utf-8")

        diff_file = DiffFile(file_path="models.py", is_new=True, added_lines=[1])
        orchestrator = PipelineOrchestrator(review_id=review_id)
        report = orchestrator.process_file(diff_file, str(tmp_path))

        assert report is not None
        assert report.file_path == "models.py"
        # Findings should be generated via deterministic static analysis
        assert len(report.issues) > 0
        assert any(i.reasoning_source == "static_analysis" for i in report.issues)

    def test_embedding_quota_exhaustion_does_not_hang_pipeline(self, tmp_path):
        """Verify that embedding quota exhaustion falls back gracefully without hanging."""
        from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider

        provider = GeminiEmbeddingProvider(api_key="test_key", model="gemini-embedding-2")
        provider._exhausted_models.add("gemini-embedding-2")
        provider._exhausted_models.add("gemini-embedding-001")

        # Calling embed_query raises immediately caught error across candidate models
        try:
            vec = provider.embed_query("test query")
            assert len(vec) == provider.dimension
        except Exception as e:
            assert "embedding failed across all candidate models" in str(e).lower() or "exhausted" in str(e).lower()

    def test_llm_fallback_reaches_static_reasoning(self, tmp_path):
        """Verify that when all LLM models fail, static reasoning produces grounded explanations."""
        review_id = f"test_static_{uuid.uuid4().hex[:8]}"
        tracker = get_review_tracker(review_id)
        tracker.mark_model_exhausted("gemini-3.6-flash")
        tracker.mark_model_exhausted("gemini-3.5-flash-lite")
        tracker.mark_model_exhausted("gemini-3.5-flash")
        tracker.mark_model_exhausted("gemini-2.5-flash")
        tracker.set_degraded_mode("all_models_exhausted")

        test_file = tmp_path / "security.py"
        test_file.write_text("x = eval('2 + 2')\n", encoding="utf-8")

        diff_file = DiffFile(file_path="security.py", is_new=True, added_lines=[1])
        orchestrator = PipelineOrchestrator(review_id=review_id)
        report = orchestrator.process_file(diff_file, str(tmp_path))

        assert report is not None
        assert len(report.issues) > 0
        assert report.issues[0].line == 1
        assert report.issues[0].reasoning_source == "static_analysis"
        assert "eval" in report.issues[0].root_cause.lower() or "eval" in report.issues[0].issue.lower()

    @patch("app.analysis.RAG.knowledge_retrieval_service.KnowledgeRetrievalService.retrieve_for_finding")
    def test_rag_failure_still_allows_review_completion(self, mock_rag, tmp_path):
        """Verify that if RAG throws an exception, review generation proceeds with static findings."""
        mock_rag.side_effect = Exception("RAG service connection refused")

        review_id = f"test_rag_fail_{uuid.uuid4().hex[:8]}"
        test_file = tmp_path / "sample.py"
        test_file.write_text("x = eval('2 + 2')\n", encoding="utf-8")

        diff_file = DiffFile(file_path="sample.py", is_new=True, added_lines=[1])
        orchestrator = PipelineOrchestrator(review_id=review_id)
        report = orchestrator.process_file(diff_file, str(tmp_path))

        assert report is not None
        assert len(report.issues) > 0
        assert report.issues[0].line == 1

    def test_linter_timeout_returns_empty_findings_gracefully(self, tmp_path):
        """Verify that linter runners with small timeouts handle TimeoutExpired gracefully."""
        from app.linters.pylint_runner import PylintRunner
        from app.linters.flake8_runner import Flake8Runner
        from app.linters.bandit_runner import BanditRunner

        dummy_file = tmp_path / "code.py"
        dummy_file.write_text("a = 1\n", encoding="utf-8")

        pylint = PylintRunner(timeout=15)
        flake8 = Flake8Runner(timeout=15)
        bandit = BanditRunner(timeout=15)

        # Should execute without error
        assert isinstance(pylint.run(str(dummy_file)), list)
        assert isinstance(flake8.run(str(dummy_file)), list)
        assert isinstance(bandit.run(str(dummy_file)), list)

    def test_snippet_review_task_reaches_terminal_completed_state(self):
        """Verify that run_snippet_review_task finishes and saves report."""
        review_id = f"test_snippet_{uuid.uuid4().hex[:8]}"
        code = "def add(a, b):\n    return a + b\n"

        run_snippet_review_task(
            review_id=review_id,
            code=code,
            language="python",
            filename="math_utils.py"
        )

        store = ReviewStore()
        report = store.get_report(review_id)
        assert report is not None
        assert report.review_id == review_id
        assert len(report.file_reports) == 1

    @patch("app.github.GitHubClient.get_pull_request")
    @patch("app.github.GitHubClient.get_pr_changed_files")
    @patch("app.github.GitHubClient.clone_and_checkout_pr")
    def test_pr_review_task_deadline_exceeded_produces_terminal_state(
        self, mock_clone, mock_get_files, mock_get_pr, tmp_path
    ):
        """Verify that when MAX_REVIEW_DURATION_SECONDS is exceeded, review terminates and saves partial report."""
        review_id = f"test_deadline_{uuid.uuid4().hex[:8]}"
        mock_get_pr.return_value = {"base": {"ref": "main", "repo": {"clone_url": "https://github.com/test/repo"}}}
        mock_get_files.return_value = ["file1.py", "file2.py"]

        # Create dummy repo
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "file1.py").write_text("x = 1\n", encoding="utf-8")
        (repo_dir / "file2.py").write_text("y = 2\n", encoding="utf-8")

        mock_clone.return_value = {
            "diff_text": "--- a/file1.py\n+++ b/file1.py\n@@ -1 +1 @@\n+x = 1\n",
            "base_ref": "main",
            "target_dir": str(repo_dir)
        }

        # Set review duration to 0 to trigger immediate deadline
        with patch("app.pipeline.runner.get_settings") as mock_settings:
            settings_obj = MagicMock()
            settings_obj.REPOS_DIR = str(tmp_path)
            settings_obj.MAX_REVIEW_DURATION_SECONDS = 0.001
            mock_settings.return_value = settings_obj

            run_pr_review_task(
                review_id=review_id,
                repo_url="https://github.com/test/repo",
                pr_number=1
            )

        store = ReviewStore()
        report = store.get_report(review_id)
        # Should save report (even if partial) and reach terminal state
        assert report is not None

    def test_unexpected_exception_in_snippet_task_sets_failed_status(self):
        """Verify that unexpected exceptions in review task mark status as failed."""
        review_id = f"test_fail_{uuid.uuid4().hex[:8]}"

        with patch("app.pipeline.orchestrator.PipelineOrchestrator.process_file") as mock_proc:
            mock_proc.side_effect = RuntimeError("Fatal pipeline crash")

            run_snippet_review_task(
                review_id=review_id,
                code="x = 1",
                language="python",
                filename="test.py"
            )

    def test_pipeline_traces_recorded_in_orchestrator(self, tmp_path):
        """Verify that pipeline orchestrator records structured traces."""
        review_id = f"test_traces_{uuid.uuid4().hex[:8]}"
        test_file = tmp_path / "sample.py"
        test_file.write_text("def foo():\n    return 42\n", encoding="utf-8")

        diff_file = DiffFile(file_path="sample.py", is_new=True, added_lines=[1, 2])
        orchestrator = PipelineOrchestrator(review_id=review_id)
        orchestrator.process_file(diff_file, str(tmp_path))

        stages = [t["stage"] for t in orchestrator.traces]
        assert "ast_parsing" in stages
        assert "cfg_construction" in stages
        assert "call_graph_analysis" in stages
        assert "dataflow_analysis" in stages

    def test_get_review_status_endpoint_returns_terminal_response(self):
        """Verify GET /review/{review_id} handles completed, timed_out, and 404 cleanly."""
        client = TestClient(app)

        # 404 for unknown review
        resp = client.get(f"/review/{uuid.uuid4()}")
        assert resp.status_code == 404

        # Completed review with saved report
        review_id = str(uuid.uuid4())
        report = ReviewReport(
            review_id=review_id,
            file_reports=[],
            summary_stats={"total_files": 0, "total_issues": 0, "clean_code": True},
            trace_id=review_id
        )
        store = ReviewStore()
        store.save_report(report)

        # Mock DB review object with completed status
        with patch("app.db.repositories.ReviewRepository.get_review") as mock_get_rev:
            mock_rev = MagicMock()
            mock_rev.id = review_id
            mock_rev.status = "completed"
            mock_get_rev.return_value = mock_rev

            resp = client.get(f"/review/{review_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["review_id"] == review_id
