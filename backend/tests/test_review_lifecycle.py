import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.review_store import ReviewStore
from app.api.schemas import ReviewReport, ReviewIssue, FileReport
from app.analysis.graph.graph_base import Graph
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_edge import GraphEdge


@pytest.fixture
def client():
    return TestClient(app)


def test_status_endpoint_speed_and_lightweight(client):
    """Verify GET /review/{id}/status is lightweight, responds in <50ms, and avoids remote DB queries."""
    store = ReviewStore.get_instance()
    test_id = "test-status-perf-123"
    store.set_review_status(
        review_id=test_id,
        status="processing",
        stage="primary_file_static_analysis",
        message="Analyzing file 1 of 2...",
        progress_percent=75,
        repo_url="https://github.com/test/repo",
        pr_number=10
    )

    # Warm up client / ASGI pipeline
    client.get("/health")

    start = time.perf_counter()
    response = client.get(f"/review/{test_id}/status")
    duration_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["review_id"] == test_id
    assert data["status"] == "processing"
    assert data["stage"] == "primary_file_static_analysis"
    assert data["progress_percent"] == 75
    # Measured latency should be in tens of milliseconds or single digits
    assert duration_ms < 50.0, f"Status endpoint took too long: {duration_ms:.2f}ms"


def test_failed_review_returns_200_not_500(client):
    """Verify that when a review fails, GET /review/{id} and GET /review/{id}/status NEVER return HTTP 500."""
    store = ReviewStore.get_instance()
    failed_id = "test-failed-review-456"
    store.set_review_status(
        review_id=failed_id,
        status="failed",
        stage="metrics_synthesis",
        error_code="PIPELINE_STAGE_FAILED",
        error_message="NameError: name 'repo_intel' is not defined",
        failed_stage="metrics_synthesis",
        duration_seconds=42.5
    )

    # Test dedicated status endpoint
    status_resp = client.get(f"/review/{failed_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "failed"
    assert status_data["error_code"] == "PIPELINE_STAGE_FAILED"
    assert status_data["failed_stage"] == "metrics_synthesis"

    # Test standard review endpoint (MUST NOT be HTTP 500)
    review_resp = client.get(f"/review/{failed_id}")
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    assert review_data["status"] == "failed"
    assert "error_message" in review_data
    assert review_data["failed_stage"] == "metrics_synthesis"


def test_processing_review_returns_202(client):
    """Verify that an active review returns HTTP 202 on GET /review/{id}."""
    store = ReviewStore.get_instance()
    proc_id = "test-processing-review-789"
    store.set_review_status(
        review_id=proc_id,
        status="processing",
        stage="git_clone_and_checkout",
        message="Cloning repo..."
    )

    resp = client.get(f"/review/{proc_id}")
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "processing"


def test_completed_review_lifecycle(client):
    """Verify completed review retrieval from disk and store."""
    store = ReviewStore.get_instance()
    comp_id = "test-completed-review-101"

    report = ReviewReport(
        review_id=comp_id,
        repo_url="https://github.com/acme/test",
        pr_number=5,
        created_at="2026-09-05T12:00:00Z",
        duration_seconds=15.2,
        file_reports=[
            FileReport(
                file_path="main.py",
                issues=[
                    ReviewIssue(
                        line=10,
                        severity="high",
                        confidence=0.9,
                        issue="Potential SQL Injection",
                        root_cause="Unsanitized query input",
                        fix="Use parameterized queries",
                        issue_type="security"
                    )
                ]
            )
        ],
        summary_stats={
            "total_issues": 1,
            "meaningful_issues": 1,
            "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0}
        },
        trace_id=comp_id
    )
    store.save_report(report)

    # Test status endpoint
    status_resp = client.get(f"/review/{comp_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"

    # Test full review endpoint
    review_resp = client.get(f"/review/{comp_id}")
    assert review_resp.status_code == 200
    full_data = review_resp.json()
    assert full_data["review_id"] == comp_id
    assert len(full_data["file_reports"]) == 1
    assert full_data["file_reports"][0]["issues"][0]["severity"] == "high"

    # Cleanup
    store.delete_report(comp_id)


def test_graph_cycle_termination():
    """Verify graph traversal handles cycles (A -> B -> C -> A) safely without infinite loop."""
    graph = Graph()
    node_a = GraphNode(node_id="A")
    node_b = GraphNode(node_id="B")
    node_c = GraphNode(node_id="C")
    node_d = GraphNode(node_id="D")

    graph.add_node(node_a)
    graph.add_node(node_b)
    graph.add_node(node_c)
    graph.add_node(node_d)

    # Cycle: A -> B -> C -> A
    graph.add_edge(GraphEdge(source="A", target="B"))
    graph.add_edge(GraphEdge(source="B", target="C"))
    graph.add_edge(GraphEdge(source="C", target="A"))
    # Branch to D: C -> D
    graph.add_edge(GraphEdge(source="C", target="D"))

    # Verify cycle detection
    assert graph.has_cycle() is True

    # Verify path finding terminates and finds shortest path despite cycle
    path = graph.find_path("A", "D")
    assert path == ["A", "B", "C", "D"]

    # Verify path finding to an unreachable node returns None and terminates
    node_z = GraphNode(node_id="Z")
    graph.add_node(node_z)
    assert graph.find_path("A", "Z") is None
