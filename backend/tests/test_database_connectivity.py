"""
CodeGuard V2 — Comprehensive Database Configuration, Connectivity & Persistence Tests.

Includes:
- Offline unit tests (configuration loading, URL normalization, driver detection,
  pooling settings, credential masking).
- Live integration tests (SELECT 1, session lifecycle, transaction commit/rollback,
  ReviewRepository, ReviewIssue, PipelineTrace persistence).
"""

import os
import uuid
import pytest
from sqlalchemy import text
from app.core.config import Settings, get_settings
from app.db.database import (
    _get_engine,
    _get_session_factory,
    _reset_engine_cache,
    SessionLocal,
    engine,
    Base,
)
from app.db.models import Review, ReviewIssueModel, PipelineTrace
from app.db.repositories import ReviewRepository


# ── Helper for Live DB Availability ──────────────────────────────────────────

def _is_live_postgres_available() -> bool:
    """Check whether a live PostgreSQL connection can be established."""
    try:
        eng = _get_engine()
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _is_live_postgres_available(),
    reason="Live PostgreSQL database is not available or reachable.",
)


# ═════════════════════════════════════════════════════════════════════════════
# 1. OFFLINE UNIT TESTS (No database connection required)
# ═════════════════════════════════════════════════════════════════════════════

class TestDatabaseConfigUnit:
    """Offline unit tests for database configuration, pooling, and safety."""

    def test_database_url_normalization_postgres_scheme(self):
        """Ensure legacy postgres:// is normalized to postgresql:// without altering driver."""
        s = Settings(
            DATABASE_URL="postgres://user:secretpass@db.example.com:5432/mydb",
            GEMINI_API_KEY="mock_key",
        )
        assert s.DATABASE_URL.startswith("postgresql://")
        assert "secretpass" in s.DATABASE_URL  # Internally retained for connection

    def test_alembic_url_normalization_and_fallback(self):
        """Ensure ALEMBIC_DATABASE_URL falls back to DATABASE_URL when unset."""
        # 1. Fallback case
        s1 = Settings(
            DATABASE_URL="postgresql://appuser:apppass@db.example.com:5432/appdb",
            GEMINI_API_KEY="mock_key",
        )
        assert s1.effective_alembic_url == s1.DATABASE_URL

        # 2. Explicit migration URL with normalization
        s2 = Settings(
            DATABASE_URL="postgresql://appuser:apppass@db.example.com:5432/appdb",
            ALEMBIC_DATABASE_URL="postgres://miguser:migpass@db.example.com:5432/appdb",
            GEMINI_API_KEY="mock_key",
        )
        assert s2.effective_alembic_url.startswith("postgresql://")
        assert "miguser" in s2.effective_alembic_url

    def test_credential_masking_utility(self):
        """Verify get_masked_database_url hides password securely."""
        s = Settings(
            DATABASE_URL="postgresql://myuser:supersecret123@aws-0.pooler.supabase.com:5432/postgres",
            GEMINI_API_KEY="mock_key",
        )
        masked = s.get_masked_database_url()
        assert "supersecret123" not in masked
        assert ":***@" in masked
        assert "myuser" in masked
        assert "aws-0.pooler.supabase.com:5432/postgres" in masked

    def test_engine_proxy_repr_masks_credentials(self):
        """Ensure engine proxy string representation never leaks credentials."""
        repr_str = repr(engine)
        assert "supersecret" not in repr_str
        assert "<Engine(" in repr_str

    def test_configurable_pool_settings(self):
        """Ensure connection pool parameters load from environment variables."""
        s = Settings(
            DB_POOL_SIZE=8,
            DB_MAX_OVERFLOW=3,
            DB_POOL_TIMEOUT=45,
            DB_POOL_RECYCLE=900,
            GEMINI_API_KEY="mock_key",
        )
        assert s.DB_POOL_SIZE == 8
        assert s.DB_MAX_OVERFLOW == 3
        assert s.DB_POOL_TIMEOUT == 45
        assert s.DB_POOL_RECYCLE == 900

    def test_postgresql_driver_detected(self):
        """Verify that psycopg2 driver is installed and supported by SQLAlchemy."""
        import psycopg2
        assert psycopg2.__version__ is not None
        
        # Test dialect resolution
        from sqlalchemy.dialects import postgresql
        dialect = postgresql.dialect()
        assert dialect.name == "postgresql"


# ═════════════════════════════════════════════════════════════════════════════
# 2. LIVE DATABASE TESTS (Require active PostgreSQL instance)
# ═════════════════════════════════════════════════════════════════════════════

@requires_postgres
class TestLiveDatabaseIntegration:
    """Integration tests verifying real operations against the PostgreSQL database."""

    def test_live_select_1_connectivity(self):
        """Verify that a basic SELECT 1 succeeds over secure transport."""
        eng = _get_engine()
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1 AS alive")).scalar()
            assert result == 1

    def test_live_session_creation(self):
        """Verify that SessionLocal creates an active SQLAlchemy Session."""
        db = SessionLocal()
        try:
            assert db.is_active
            result = db.execute(text("SELECT current_database()")).scalar()
            assert result is not None
        finally:
            db.close()

    def test_live_transaction_commit_and_rollback(self):
        """Verify transaction commit and rollback behaviors."""
        db = SessionLocal()
        test_id = f"tx_test_{uuid.uuid4().hex[:8]}"
        try:
            # 1. Rollback test
            review_rollback = Review(
                id=f"{test_id}_rb",
                repo_url="https://github.com/example/rollback",
                pr_number=99,
                status="pending"
            )
            db.add(review_rollback)
            db.rollback()

            found = db.query(Review).filter(Review.id == f"{test_id}_rb").first()
            assert found is None

            # 2. Commit test
            review_commit = Review(
                id=f"{test_id}_cm",
                repo_url="https://github.com/example/commit",
                pr_number=100,
                status="started"
            )
            db.add(review_commit)
            db.commit()

            found = db.query(Review).filter(Review.id == f"{test_id}_cm").first()
            assert found is not None
            assert found.status == "started"

        finally:
            # Cleanup
            db.query(Review).filter(Review.id.in_([f"{test_id}_rb", f"{test_id}_cm"])).delete()
            db.commit()
            db.close()

    def test_live_review_repository_crud_lifecycle(self):
        """Verify ReviewRepository methods: create_review, update_status, get_review."""
        db = SessionLocal()
        repo = ReviewRepository(db)
        review_id = f"repo_test_{uuid.uuid4().hex[:8]}"

        try:
            # Create
            created = repo.create_review(
                review_id=review_id,
                repo_url="https://github.com/codeguard/test",
                pr_number=42
            )
            assert created.id == review_id
            assert created.status == "started"

            # Retrieve
            fetched = repo.get_review(review_id)
            assert fetched is not None
            assert fetched.pr_number == 42

            # Update status
            repo.update_status(review_id, "completed")
            updated = repo.get_review(review_id)
            assert updated.status == "completed"

        finally:
            db.query(Review).filter(Review.id == review_id).delete()
            db.commit()
            db.close()

    def test_live_review_issue_persistence_with_jsonb(self):
        """Verify ReviewIssueModel persistence including JSONB fields."""
        db = SessionLocal()
        repo = ReviewRepository(db)
        review_id = f"issue_test_{uuid.uuid4().hex[:8]}"

        try:
            repo.create_review(review_id, "https://github.com/codeguard/test", 1)

            issue_data = {
                "line": 42,
                "severity": "critical",
                "confidence": 0.95,
                "issue": "SQL Injection vulnerability in query builder",
                "root_cause": "User input concatenated directly into raw SQL string",
                "trigger_condition": "When malicious payload contains quote escape",
                "fix": "Use parameterized queries with bind variables",
                "patch": "- query = f'SELECT * FROM u WHERE id={id}'\n+ query = 'SELECT * FROM u WHERE id=:id'",
                "issue_type": "security",
                "sources": ["ast", "dataflow"],
                "reasoning_trace": [
                    {"step": 1, "thought": "Identified tainted source from request handler"},
                    {"step": 2, "thought": "Followed propagation to cursor.execute sink"}
                ],
                "evidence": {
                    "source_line": 10,
                    "sink_line": 42,
                    "tainted_var": "user_id"
                }
            }

            repo.save_issue(review_id, "app/api/users.py", issue_data)

            # Query back
            saved_issue = db.query(ReviewIssueModel).filter(ReviewIssueModel.review_id == review_id).first()
            assert saved_issue is not None
            assert saved_issue.file_path == "app/api/users.py"
            assert saved_issue.severity == "critical"
            assert saved_issue.confidence == 0.95
            assert saved_issue.sources == ["ast", "dataflow"]
            assert len(saved_issue.reasoning_trace) == 2
            assert saved_issue.evidence["tainted_var"] == "user_id"

        finally:
            db.query(ReviewIssueModel).filter(ReviewIssueModel.review_id == review_id).delete()
            db.query(Review).filter(Review.id == review_id).delete()
            db.commit()
            db.close()

    def test_live_pipeline_trace_persistence(self):
        """Verify PipelineTrace persistence with duration and JSONB input/output payloads."""
        db = SessionLocal()
        repo = ReviewRepository(db)
        review_id = f"trace_test_{uuid.uuid4().hex[:8]}"

        try:
            repo.create_review(review_id, "https://github.com/codeguard/test", 2)

            trace = repo.save_trace(
                review_id=review_id,
                stage="static_analysis_ast",
                duration_ms=123.45,
                input_data={"file_count": 3, "language": "python"},
                output_data={"findings_count": 5, "parse_errors": 0}
            )

            assert trace.id is not None
            assert trace.stage == "static_analysis_ast"
            assert trace.duration_ms == 123.45

            # Query back
            saved_trace = db.query(PipelineTrace).filter(PipelineTrace.id == trace.id).first()
            assert saved_trace is not None
            assert saved_trace.input_data["file_count"] == 3
            assert saved_trace.output_data["findings_count"] == 5

        finally:
            db.query(PipelineTrace).filter(PipelineTrace.review_id == review_id).delete()
            db.query(Review).filter(Review.id == review_id).delete()
            db.commit()
            db.close()
