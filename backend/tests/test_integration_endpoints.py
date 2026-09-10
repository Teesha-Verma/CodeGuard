"""
Integration tests for CodeGuard V2 extension endpoints:
- Review History & Dashboard Stats
- Playground Synchronous Re-analysis
- AI Assistant Chat
- Contextual Learner Mode
- Security Health & Risk
- Knowledge Base Topics
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "llm" in data


def test_review_history_and_stats():
    # 1. Review history list
    resp = client.get("/review?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "reviews" in data
    assert isinstance(data["reviews"], list)

    # 2. Review summary stats
    resp_stats = client.get("/review/summary/stats")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    assert "total_reviews" in stats
    assert "total_issues" in stats
    assert "critical_count" in stats


def test_playground_analysis_clean_code():
    clean_code = (
        "def safe_query(user_id):\n"
        "    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))\n"
        "    return cursor.fetchall()\n"
    )
    resp = client.post("/review/playground", json={
        "code": clean_code,
        "language": "python",
        "filename": "test_clean.py"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["is_resolved"] is True


def test_playground_analysis_vulnerable_code():
    vulnerable_code = (
        "def bad_query(user_id):\n"
        "    query = f'SELECT * FROM users WHERE id = {user_id}'\n"
        "    cursor.execute(query)\n"
        "    return cursor.fetchall()\n"
    )
    resp = client.post("/review/playground", json={
        "code": vulnerable_code,
        "language": "python",
        "filename": "test_vuln.py",
        "original_finding_line": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "still_detected"
    assert data["is_resolved"] is False


def test_assistant_chat():
    resp = client.post("/assistant/chat", json={
        "messages": [
            {"role": "user", "content": "How do I fix SQL injection in Python?"}
        ],
        "context": "Flask application with PostgreSQL database"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert "provider" in data


def test_learner_finding():
    resp = client.post("/learn/finding", json={
        "file_path": "app/db.py",
        "line": 15,
        "issue_text": "SQL Injection detected via formatted query",
        "category": "Injection"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "concept" in data
    assert "why_it_matters" in data
    assert "how_to_fix" in data
    assert "quiz" in data
    assert len(data["quiz"]["options"]) == 4


def test_security_health_and_risk():
    health_resp = client.get("/security/health")
    assert health_resp.status_code == 200
    hdata = health_resp.json()
    assert 0 <= hdata["score"] <= 100
    assert hdata["grade"] in ("A", "B", "C", "D", "F")
    assert "formula" in hdata

    risk_resp = client.get("/security/risk")
    assert risk_resp.status_code == 200
    rdata = risk_resp.json()
    assert rdata["overall_risk"] in ("critical", "high", "medium", "low")
    assert isinstance(rdata["ranked_files"], list)


def test_knowledge_topics():
    list_resp = client.get("/knowledge/topics")
    assert list_resp.status_code == 200
    topics = list_resp.json()
    assert len(topics) >= 5
    assert any(t["id"] == "sql-injection" for t in topics)

    detail_resp = client.get("/knowledge/topics/sql-injection")
    assert detail_resp.status_code == 200
    topic = detail_resp.json()
    assert topic["id"] == "sql-injection"
    assert "vulnerable_example" in topic
    assert "preventive_guidelines" in topic
    assert len(topic["preventive_guidelines"]) > 0
