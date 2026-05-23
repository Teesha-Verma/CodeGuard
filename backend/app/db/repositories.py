from sqlalchemy.orm import Session
from app.db.models import Review, ReviewIssueModel, PipelineTrace
import uuid
from typing import Optional

class ReviewRepository:
    """Repository pattern for database operations related to code reviews."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_review(self, review_id: str, repo_url: str, pr_number: int) -> Review:
        review = Review(id=review_id, repo_url=repo_url, pr_number=pr_number, status="started")
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
        
    def update_status(self, review_id: str, status: str):
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.status = status
            self.db.commit()
            
    def save_issue(self, review_id: str, file_path: str, issue_data: dict):
        issue_id = str(uuid.uuid4())
        
        # Preserve new fields inside evidence column for complete database backward compatibility
        evidence = issue_data.get("evidence", {}) or {}
        evidence["signal_priority"] = issue_data.get("signal_priority", "medium")
        evidence["issue_category"] = issue_data.get("issue_category", "runtime logic risks")
        evidence["is_low_signal"] = issue_data.get("is_low_signal", False)
        evidence["detection_source"] = issue_data.get("detection_source", "ast")
        evidence["reasoning_source"] = issue_data.get("reasoning_source", "static_analysis")
        evidence["priority_score"] = issue_data.get("priority_score", 0.50)
        evidence["detection_sources"] = issue_data.get("detection_sources", [])

        issue = ReviewIssueModel(
            id=issue_id,
            review_id=review_id,
            file_path=file_path,
            line_number=issue_data.get("line"),
            severity=issue_data.get("severity"),
            confidence=issue_data.get("confidence"),
            issue_description=issue_data.get("issue"),
            root_cause=issue_data.get("root_cause"),
            trigger_condition=issue_data.get("trigger_condition"),
            fix_suggestion=issue_data.get("fix"),
            patch=issue_data.get("patch"),
            issue_type=issue_data.get("issue_type"),
            sources=issue_data.get("sources"),
            reasoning_trace=issue_data.get("reasoning_trace"),
            evidence=evidence
        )
        self.db.add(issue)
        self.db.commit()

    def get_review(self, review_id: str) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def save_trace(self, review_id: str, stage: str, duration_ms: float, input_data: dict, output_data: dict) -> PipelineTrace:
        trace_id = str(uuid.uuid4())
        trace = PipelineTrace(
            id=trace_id,
            review_id=review_id,
            stage=stage,
            duration_ms=duration_ms,
            input_data=input_data,
            output_data=output_data
        )
        self.db.add(trace)
        self.db.commit()
        return trace
