def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "CodeGuard AI Engine" in response.json()["message"]

def test_snippet_review(client):
    payload = {
        "files": [
            {
                "file_path": "test.py",
                "code_snippet": "def foo(x=[]):\n    x.append(1)\n    return x",
                "changed_lines": [1, 2]
            }
        ]
    }
    response = client.post("/review/snippet", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "review_id" in data
    assert len(data["file_reports"]) == 1
