import os
import uuid
from app.db.database import SessionLocal, Base, engine
from app.db.repositories import ReviewRepository
from app.db.models import Review, PipelineTrace, ReviewIssueModel
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile


def test_database_trace_saving():
    """Verify that save_trace creates trace records in the database."""
    db = SessionLocal()
    repo = ReviewRepository(db)
    
    # 1. Create a dummy review
    review_id = f"test_trace_{uuid.uuid4().hex[:8]}"
    review = repo.create_review(review_id, "https://github.com/example/repo", 42)
    
    try:
        # 2. Save a dummy trace
        trace = repo.save_trace(
            review_id=review_id,
            stage="ast_parsing",
            duration_ms=45.2,
            input_data={"file": "foo.py"},
            output_data={"rules": ["nested_loops"]}
        )
        
        assert trace.id is not None
        assert trace.review_id == review_id
        assert trace.stage == "ast_parsing"
        assert trace.duration_ms == 45.2
        assert trace.input_data == {"file": "foo.py"}
        assert trace.output_data == {"rules": ["nested_loops"]}
        
        # 3. Retrieve from DB
        db_trace = db.query(PipelineTrace).filter(PipelineTrace.id == trace.id).first()
        assert db_trace is not None
        assert db_trace.stage == "ast_parsing"
        assert db_trace.duration_ms == 45.2
        
    finally:
        # Cleanup
        db.query(PipelineTrace).filter(PipelineTrace.review_id == review_id).delete()
        db.query(Review).filter(Review.id == review_id).delete()
        db.commit()
        db.close()


def test_orchestrator_and_generator_trace_generation():
    """Verify that PipelineOrchestrator generates and accumulates traces."""
    review_id = f"test_orch_{uuid.uuid4().hex[:8]}"
    orchestrator = PipelineOrchestrator(review_id=review_id)
    
    # Simulating simple code review
    code = "def mutate_list():\n    items = [1, 2, 3]\n    for i in items:\n        items.remove(i)\n"
    diff_file = DiffFile(
        file_path="snippet.py",
        is_new=True,
        added_lines=[1, 2, 3, 4]
    )
    
    # Create virtual repo structure
    temp_dir = os.path.join("repos", f"temp_{review_id}")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, "snippet.py")
    
    try:
        with open(file_path, "w") as f:
            f.write(code)
            
        report = orchestrator.process_file(diff_file, temp_dir)
        
        # Check that traces are recorded
        assert len(orchestrator.traces) >= 2
        
        # 1. AST Parsing trace
        ast_trace = next((t for t in orchestrator.traces if t["stage"] == "ast_parsing"), None)
        assert ast_trace is not None
        assert "rules_executed" in ast_trace["output_data"]
        assert "eval_detection" in ast_trace["output_data"]["rules_executed"]
        
        # 2. Confidence and Grounding trace
        conf_trace = next((t for t in orchestrator.traces if t["stage"] == "confidence_and_grounding"), None)
        assert conf_trace is not None
        assert "arithmetic_steps" in conf_trace["output_data"]
        assert "source_attributions" in conf_trace["output_data"]
        
        # Check newly populated ReviewIssue fields
        assert len(report.meaningful_issues) > 0
        issue = report.meaningful_issues[0]
        assert issue.signal_priority == "high"
        assert issue.issue_category == "mutation risks"
        assert issue.is_low_signal is False
        assert issue.detection_source == "ast"
        assert issue.reasoning_source == "llm"
        
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
