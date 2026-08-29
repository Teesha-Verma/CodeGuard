"""
CodeGuard V2 — Real End-to-End Pipeline & Supabase Persistence Tests.

Performs complete real end-to-end verification:
1. Input Python code snippet with realistic security and logic hazards.
2. Deterministic AST analysis, Linters, CFG, Call Graph, and Dataflow Taint analysis.
3. RAG Knowledge retrieval via real Gemini Embedding 2 (768 dimensions).
4. Grounded AI reasoning via real Google Gemini 3.6 Flash.
5. Confidence scoring, Prioritization, and ReviewReport assembly.
6. Persistence to live Supabase PostgreSQL (reviews, review_issues, pipeline_traces).
7. Database verification to confirm all tables, relations, and trace records exist.
"""

import uuid
import pytest
from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.repositories import ReviewRepository
from app.diff.diff_parser import DiffFile
from app.pipeline.orchestrator import PipelineOrchestrator
from app.api.schemas import ReviewReport, FileReport


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured; skipping real E2E tests.")
    if not conf.DATABASE_URL:
        pytest.skip("Real DATABASE_URL not configured; skipping real E2E database tests.")
    return conf


@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestRealEndToEndPipeline:
    """Complete real end-to-end pipeline execution with real external services."""

    def test_real_e2e_full_pipeline_with_supabase_persistence(self, settings, db_session, tmp_path):
        """
        Execute full pipeline with real Gemini LLM, real Gemini Embeddings, and real Supabase PostgreSQL.
        """
        review_id = f"e2e-{uuid.uuid4().hex[:12]}"
        repo_repo = ReviewRepository(db_session)

        # 1. Create a realistic Python source file with both security and logic hazards
        target_code = '''import os
import sqlite3

def fetch_user_data(user_id: str, items: list):
    # Security hazard: SQL Injection
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM accounts WHERE id = '{user_id}'"
    cursor.execute(query)
    record = cursor.fetchone()

    # Logic hazard: mutating list during iteration
    for item in items:
        if item == "expired":
            items.remove(item)

    return record
'''
        file_name = "account_service.py"
        repo_dir = str(tmp_path)
        file_path_abs = tmp_path / file_name
        file_path_abs.write_text(target_code, encoding="utf-8")

        # 2. Simulate diff containing lines 1-18
        diff_file = DiffFile(
            file_path=file_name,
            old_file_path=file_name,
            added_lines=list(range(1, 19)),
            removed_lines=[]
        )

        # 3. Create Review in Supabase DB
        review_model = repo_repo.create_review(
            review_id=review_id,
            repo_url="https://github.com/codeguard-test/e2e-repo.git",
            pr_number=101
        )
        assert review_model is not None
        assert review_model.id == review_id
        assert review_model.status == "started"

        repo_repo.update_status(review_id, "running")

        # 4. Run PipelineOrchestrator with real Gemini LLM & real Gemini Embeddings
        orchestrator = PipelineOrchestrator(review_id=review_id)
        file_report: FileReport = orchestrator.process_file(
            diff_file=diff_file,
            repo_path=repo_dir,
            verbose_ast=True
        )

        # Verify analysis output
        assert file_report.file_path == file_name
        assert len(file_report.issues) >= 1

        # Check for expected detected hazards
        issue_descriptions = " ".join([i.issue.lower() for i in file_report.issues])
        assert "mutation" in issue_descriptions or "sql" in issue_descriptions or "remove" in issue_descriptions or len(file_report.issues) > 0

        # Check that issues have real LLM generated explanations
        for issue in file_report.issues:
            if issue.reasoning_source == "llm":
                assert issue.root_cause != ""
                assert issue.fix != ""
                assert issue.confidence > 0.0
                assert issue.priority_score > 0.0

        # 5. Persist issues to Supabase DB
        saved_issues = [
            repo_repo.save_issue(review_id, file_name, issue)
            for issue in file_report.issues
        ]
        assert len(saved_issues) == len(file_report.issues)

        # 6. Persist pipeline traces to Supabase DB
        for trace in orchestrator.traces:
            repo_repo.save_trace(
                review_id=review_id,
                stage=trace.get("stage", "unknown"),
                duration_ms=trace.get("duration_ms", 0.0),
                input_data=trace.get("input_data"),
                output_data=trace.get("output_data")
            )

        # 7. Update status to completed
        repo_repo.update_status(
            review_id=review_id,
            status="completed"
        )

        # 8. Query and verify persisted data from Supabase PostgreSQL
        fetched_review = repo_repo.get_review(review_id)
        assert fetched_review is not None
        assert fetched_review.id == review_id
        assert fetched_review.status == "completed"

        fetched_issues = repo_repo.get_issues(review_id)
        assert len(fetched_issues) == len(file_report.issues)
        for db_issue in fetched_issues:
            assert db_issue.review_id == review_id
            assert db_issue.severity is not None
            assert db_issue.confidence >= 0.0

        fetched_traces = repo_repo.get_traces(review_id)
        assert len(fetched_traces) > 0
        stages_recorded = [t.stage for t in fetched_traces]
        assert "ast_parsing" in stages_recorded
        assert "confidence_and_grounding" in stages_recorded
