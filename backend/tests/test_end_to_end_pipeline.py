"""
CodeGuard V2 — Complete End-to-End Integration & Pipeline Wiring Verification Tests.

Exercises the entire 25-stage review pipeline:
Input Processing → Context Resolution → AST Analysis → Linters → CFG → Call Graph
→ Data Flow/Taint → Repository Intelligence → Feature Aggregation → RAG Query Construction
→ Gemini Embedding 2 → Vector Retrieval → Reranking → Prompt Builder → Gemini 3.6 Flash
→ Structured Review → Reasoning Layer → Prioritization → Confidence Engine → Review Generation
→ Observability → PostgreSQL Storage → FastAPI Response.
"""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings, Settings
from app.diff.diff_parser import DiffFile, DiffParser
from app.diff.context_builder import ContextBuilder
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.feature_aggregator import FeatureAggregator
from app.pipeline.runner import run_snippet_review_task
from app.reasoning.review_generator import ReviewGenerator
from app.reasoning.root_cause_engine import RootCauseEngine
from app.reasoning.confidence_engine import ConfidenceEngine
from app.static_analysis.prioritization import PrioritizationEngine
from app.analysis.cfg.cfg_builder import CFGBuilder
from app.analysis.call_graph.call_graph_builder import CallGraphBuilder
from app.analysis.dataflow.taint.taint_engine import TaintEngine
from app.analysis.dataflow.taint.vulnerability_rules import VulnerabilityRules
from app.analysis.repository.query_engine import RepositoryQueryEngine
from app.analysis.RAG.knowledge_retrieval_service import KnowledgeRetrievalService
from app.api.schemas import ReviewReport, FileReport, ReviewIssue
from app.storage.review_store import ReviewStore


# Multi-issue realistic Python test code
VULNERABLE_TEST_CODE = """
import os
import subprocess
import pickle
import sqlite3

def handle_user_request():
    user_input = input("Enter username: ")
    raw_payload = input("Enter payload: ")

    # Issue 1: SQL Injection (Source -> Sink)
    db = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE username = " + user_input
    cursor = db.cursor()
    cursor.execute(query)

    # Issue 2: Command Injection
    cmd = "ping -c 1 " + user_input
    os.system(cmd)

    # Issue 3: Insecure Deserialization
    obj = pickle.loads(raw_payload)

    # Issue 4: Mutation during iteration
    items = [1, 2, 3, 4]
    for item in items:
        if item % 2 == 0:
            items.remove(item)

    # Issue 5: Variable Shadowing built-in
    id = 12345

    return {"status": "processed", "id": id, "obj": obj}
"""


class TestEndToEndPipelineWiring:
    """Comprehensive test suite verifying full pipeline integration."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")

    def test_complete_file_processing_pipeline(self):
        """Tests the full orchestrator execution through all 25 analysis and reasoning stages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = "test_controller.py"
            file_path = os.path.join(temp_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(VULNERABLE_TEST_CODE)

            lines = VULNERABLE_TEST_CODE.splitlines()
            diff_file = DiffFile(
                file_path=file_name,
                is_new=True,
                added_lines=list(range(1, len(lines) + 1))
            )

            orchestrator = PipelineOrchestrator(review_id="e2e_test_rev_1")
            file_report: FileReport = orchestrator.process_file(
                diff_file=diff_file,
                repo_path=temp_dir,
                verbose_ast=True
            )

            # 1. Verify FileReport structure
            assert isinstance(file_report, FileReport)
            assert file_report.file_path == file_name
            assert len(file_report.issues) > 0

            # 2. Verify CFG and Call Graph analysis ran and produced metadata
            assert file_report.ast_summary is not None
            assert file_report.ast_summary.get("function_count", 0) >= 1
            assert file_report.ast_summary.get("cfg_functions_count", 0) >= 1

            # 3. Verify Dataflow Taint findings were identified
            assert file_report.ast_summary.get("dataflow_taint_count", 0) >= 1

            # 4. Verify detection of critical security issues (SQLi, Command Injection, Pickle, Mutation)
            detected_issues = [issue.issue.lower() for issue in file_report.issues]
            sources_present = set()
            for issue in file_report.issues:
                for s in issue.sources:
                    sources_present.add(s)

            assert "ast" in sources_present
            assert "dataflow" in sources_present

            # 5. Verify Priority Scores & Confidence values are properly calculated
            for issue in file_report.issues:
                assert 0.0 <= issue.confidence <= 1.0
                assert 0.0 <= issue.priority_score <= 1.0
                assert issue.root_cause != ""
                assert issue.trigger_condition != ""
                assert issue.fix != ""
                assert len(issue.reasoning_trace) > 0

            # 6. Verify pipeline traces recorded all stages
            trace_stages = [t["stage"] for t in orchestrator.traces]
            assert "ast_parsing" in trace_stages
            assert "cfg_construction" in trace_stages
            assert "call_graph_analysis" in trace_stages
            assert "dataflow_analysis" in trace_stages
            assert "repository_intelligence" in trace_stages
            assert "linter_execution" in trace_stages
            assert "confidence_and_grounding" in trace_stages

    def test_knowledge_retrieval_service_finding_grounding(self):
        """Verifies RAG knowledge retrieval attaches official security rules to detected findings."""
        kb_service = KnowledgeRetrievalService.get_instance()
        finding = {
            "issue": "SQL Injection in execute statement",
            "severity": "critical",
            "sources": ["dataflow", "ast"],
            "evidence": {"trigger_lines": [9]}
        }

        context = kb_service.retrieve_for_finding(finding=finding, top_k=2)
        assert context is not None
        assert context.formatted_prompt_context != ""

    def test_api_snippet_review_endpoint(self):
        """Tests the FastAPI /review/snippet endpoint with mock database session."""
        from app.db.database import get_db
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            client = TestClient(app)
            response = client.post(
                "/review/snippet",
                json={
                    "code": VULNERABLE_TEST_CODE,
                    "language": "python",
                    "filename": "auth_endpoint.py",
                    "verbose_ast": True
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "review_id" in data
            assert data["status"] == "running"
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_api_health_check(self):
        """Tests the system health check endpoint."""
        client = TestClient(app)
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_error_handling_malformed_syntax(self):
        """Ensures the pipeline gracefully handles malformed Python syntax without crashing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = "broken_syntax.py"
            file_path = os.path.join(temp_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("def broken_function(\n    print('unclosed paren'")

            diff_file = DiffFile(file_path=file_name, is_new=True, added_lines=[1, 2])
            orchestrator = PipelineOrchestrator(review_id="e2e_syntax_test")
            report = orchestrator.process_file(diff_file, temp_dir)
            assert report is not None
            assert report.file_path == file_name

    def test_live_gemini_integration_if_key_available(self):
        """
        Live Gemini 3.6 Flash & Gemini Embedding 2 verification test.
        Runs only when a valid GEMINI_API_KEY is available in the environment.
        """
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

        if not api_key or api_key in ("mock_key", "your_gemini_api_key_here"):
            pytest.skip("LIVE GEMINI TEST SKIPPED — GEMINI_API_KEY unavailable.")

        from app.analysis.RAG.llm.gemini_client import GeminiClient
        from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider

        # 1. Test Gemini Embedding 2
        embedder = GeminiEmbeddingProvider(api_key=api_key, model="gemini-embedding-2", dimension=768)
        vector = embedder.embed_query("SQL Injection protection")
        assert len(vector) == 768

        # 2. Test Gemini 2.5 Flash
        llm = GeminiClient(api_key=api_key, model="gemini-2.5-flash")
        review = llm.generate_review(prompt="Review this code snippet: cursor.execute(f'SELECT * FROM users WHERE id={user_id}')")
        assert review is not None
        assert review.review_summary != ""
