import pytest
from sqlalchemy import text
from app.db.database import _get_engine


def _pg_available() -> bool:
    """Check if a PostgreSQL connection can be established."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _pg_available(),
    reason="PostgreSQL is not available",
)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["service"] == "CodeGuard"


@requires_postgres
def test_snippet_review(client):
    payload = {
        "code": "def foo(x=[]):\n    x.append(1)\n    return x",
        "filename": "test.py",
        "language": "python"
    }
    response = client.post("/review/snippet", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "review_id" in data
