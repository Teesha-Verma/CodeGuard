"""
CodeGuard V2 — Real Production API End-to-End Test Suite.

Validates the full HTTP pipeline:
REAL CLIENT -> FASTAPI API -> GITHUB API -> PIPELINE -> RAG -> GEMINI LLM -> REASONING -> SUPABASE -> FINAL HTTP RESPONSE
"""

import time
import uuid
import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.db.database import SessionLocal, _get_engine
from app.db.repositories import ReviewRepository
from app.db.models import Review, ReviewIssueModel, PipelineTrace


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured in .env; skipping real API tests.")
    if not conf.GITHUB_TOKEN or conf.GITHUB_TOKEN in ("your_github_token_here", "mock_token"):
        pytest.skip("Real GITHUB_TOKEN not configured in .env; skipping real API tests.")
    return conf


@pytest.fixture
def http_client():
    """TestClient that executes FastAPI endpoints with background tasks."""
    return TestClient(app)


class TestRealProductionAPI:
    """End-to-end production API verification suite."""

    def test_01_health_endpoint_http(self, http_client, settings):
        """Phase 3: Verify /health returns 200, service details, and no secrets."""
        response = http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("service") == settings.APP_NAME
        assert data.get("version") == settings.APP_VERSION

        # Security check: Ensure no secret strings in response
        raw_text = response.text
        assert settings.GEMINI_API_KEY not in raw_text
        assert settings.GITHUB_TOKEN not in raw_text

    def test_02_real_snippet_review_api_workflow(self, http_client, settings):
        """
        Phase 10: Verify real snippet review workflow through HTTP API.
        Client -> POST /review/snippet -> FastAPI -> AST -> Taint -> RAG -> Gemini -> Supabase -> GET /review/{id}
        """
        vulnerable_code = '''import os
import sqlite3

def find_user_profile(user_query: str, active_sessions: list):
    # Security vulnerability: SQL injection via format string
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    sql = f"SELECT id, username, email FROM profiles WHERE username = '{user_query}'"
    cur.execute(sql)
    user = cur.fetchone()

    # Logic vulnerability: modifying collection during iteration
    for session in active_sessions:
        if session.get("expired"):
            active_sessions.remove(session)

    return user
'''
        payload = {
            "code": vulnerable_code,
            "language": "python",
            "filename": "user_service.py",
            "verbose_ast": True
        }

        # 1. Submit snippet review via HTTP POST
        post_resp = http_client.post("/review/snippet", json=payload)
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        assert "review_id" in post_data
        assert post_data["status"] == "running"
        review_id = post_data["review_id"]

        # 2. Fetch completed review report via HTTP GET
        get_resp = http_client.get(f"/review/{review_id}")
        assert get_resp.status_code == 200, f"Expected completed review report, got {get_resp.status_code}: {get_resp.text}"
        report_data = get_resp.json()

        # 3. Verify ReviewReport structure
        assert report_data.get("review_id") == review_id
        assert "file_reports" in report_data
        assert len(report_data["file_reports"]) >= 1
        file_report = report_data["file_reports"][0]
        assert file_report["file_path"] == "user_service.py"

        # 4. Verify issues and grounded Gemini root cause analysis
        meaningful_issues = file_report.get("meaningful_issues", [])
        assert len(meaningful_issues) >= 1

        first_issue = meaningful_issues[0]
        assert "line" in first_issue
        assert "severity" in first_issue
        assert "confidence" in first_issue
        assert "sources" in first_issue
        assert "root_cause" in first_issue
        assert "fix" in first_issue

        # Verify AI root cause content quality
        assert len(first_issue["root_cause"]) > 5
        assert len(first_issue["fix"]) > 5

        # 5. Verify Supabase PostgreSQL persistence
        db = SessionLocal()
        try:
            repo_repo = ReviewRepository(db)
            db_review = repo_repo.get_review(review_id)
            assert db_review is not None
            assert db_review.status == "completed"

            # Verify persisted issues in DB
            db_issues = repo_repo.get_issues(review_id)
            assert len(db_issues) >= 1

            # Verify persisted pipeline traces in DB
            db_traces = repo_repo.get_traces(review_id)
            assert len(db_traces) >= 3
            trace_stages = [t.stage for t in db_traces]
            assert "ast_parsing" in trace_stages or "linter_execution" in trace_stages
        finally:
            db.close()

        # 6. Verify no credentials leaked in HTTP response
        assert settings.GEMINI_API_KEY not in get_resp.text
        assert settings.GITHUB_TOKEN not in get_resp.text

    def test_03_real_github_pr_api_workflow(self, http_client, settings):
        """
        Phase 4-9: Verify real GitHub PR review through HTTP API.
        Client -> POST /review/pr -> FastAPI -> GitHub API -> Diff -> AST -> Linters -> CFG -> CallGraph -> Taint -> RAG -> Gemini -> Supabase -> GET /review/{id}
        """
        owner = settings.E2E_GITHUB_OWNER or "octocat"
        repo = settings.E2E_GITHUB_REPO or "Hello-World"
        pr_number = settings.E2E_GITHUB_PR_NUMBER or 1

        payload = {
            "repo_url": f"https://github.com/{owner}/{repo}",
            "pr_number": pr_number,
            "verbose_ast": True
        }

        # 1. Submit PR review via HTTP POST
        post_resp = http_client.post("/review/pr", json=payload)
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        assert "review_id" in post_data
        assert post_data["status"] == "running"
        review_id = post_data["review_id"]

        # 2. Fetch completed review report via HTTP GET
        get_resp = http_client.get(f"/review/{review_id}")
        assert get_resp.status_code == 200, f"Expected completed review report, got {get_resp.status_code}: {get_resp.text}"
        report_data = get_resp.json()

        # 3. Verify ReviewReport structure
        assert report_data.get("review_id") == review_id
        assert "file_reports" in report_data
        assert "summary_stats" in report_data

        # 4. Verify Supabase PostgreSQL persistence
        db = SessionLocal()
        try:
            repo_repo = ReviewRepository(db)
            db_review = repo_repo.get_review(review_id)
            assert db_review is not None
            assert db_review.status == "completed"
            assert db_review.pr_number == pr_number

            # Verify traces in DB
            db_traces = repo_repo.get_traces(review_id)
            assert len(db_traces) >= 1
        finally:
            db.close()

        # 5. Verify security
        assert settings.GEMINI_API_KEY not in get_resp.text
        assert settings.GITHUB_TOKEN not in get_resp.text

    def test_04_api_error_handling_and_validation(self, http_client, settings):
        """Phase 11: Verify HTTP status codes and error responses for invalid requests."""
        # 1. Non-existent review ID -> 404
        bad_id = str(uuid.uuid4())
        resp = http_client.get(f"/review/{bad_id}")
        assert resp.status_code == 404
        assert "Review not found" in resp.json().get("detail", "")

        # 2. Missing required fields in POST /review/pr -> 422 Unprocessable Entity
        resp = http_client.post("/review/pr", json={"repo_url": "https://github.com/foo/bar"})
        assert resp.status_code == 422

        # 3. Malformed JSON payload -> 422
        resp = http_client.post(
            "/review/pr",
            content="not a json",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422

        # 4. Missing required fields in POST /review/snippet -> 422
        resp = http_client.post("/review/snippet", json={"language": "python"})
        assert resp.status_code == 422

        # 5. Verify app remains healthy after error requests
        health = http_client.get("/health")
        assert health.status_code == 200
        assert health.json().get("status") == "ok"
