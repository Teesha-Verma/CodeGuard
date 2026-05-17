def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["service"] == "CodeGuard"

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
