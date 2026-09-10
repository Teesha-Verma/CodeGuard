from sqlalchemy.orm import Session
from app.db.models import Review, ReviewIssueModel, PipelineTrace
import uuid
from typing import Optional, Any, List, Dict

class ReviewRepository:
    """Repository pattern for database operations related to code reviews."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_review(self, review_id: str, repo_url: str, pr_number: int) -> Review:
        review = Review(id=review_id, repo_url=repo_url, pr_number=pr_number, status="started")
        try:
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)
        except Exception:
            self.db.rollback()
            raise
        return review
        
    def update_status(self, review_id: str, status: str):
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if review:
            try:
                review.status = status
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
            
    def save_issue(self, review_id: str, file_path: str, issue_data: Any, finding_category: str = "meaningful") -> ReviewIssueModel:
        issue_id = str(uuid.uuid4())

        if hasattr(issue_data, "model_dump"):
            data = issue_data.model_dump()
        elif hasattr(issue_data, "dict"):
            data = issue_data.dict()
        elif isinstance(issue_data, dict):
            data = issue_data
        else:
            data = vars(issue_data)

        # Preserve new fields inside evidence column for complete database backward compatibility
        evidence = data.get("evidence", {}) or {}
        if not isinstance(evidence, dict):
            evidence = {}
        evidence["signal_priority"] = data.get("signal_priority", "medium")
        evidence["issue_category"] = data.get("issue_category", "runtime logic risks")
        evidence["is_low_signal"] = data.get("is_low_signal", False)
        evidence["detection_source"] = data.get("detection_source", "ast")
        evidence["reasoning_source"] = data.get("reasoning_source", "static_analysis")
        evidence["priority_score"] = data.get("priority_score", 0.50)
        evidence["detection_sources"] = data.get("detection_sources", [])
        evidence["finding_category"] = finding_category
        evidence["llm_provider"] = data.get("llm_provider")
        evidence["llm_model"] = data.get("llm_model")

        issue = ReviewIssueModel(
            id=issue_id,
            review_id=review_id,
            file_path=file_path,
            line_number=data.get("line"),
            severity=data.get("severity"),
            confidence=data.get("confidence"),
            issue_description=data.get("issue"),
            root_cause=data.get("root_cause"),
            trigger_condition=data.get("trigger_condition"),
            fix_suggestion=data.get("fix"),
            patch=data.get("patch"),
            issue_type=data.get("issue_type"),
            sources=data.get("sources"),
            reasoning_trace=data.get("reasoning_trace"),
            evidence=evidence
        )
        try:
            self.db.add(issue)
            self.db.commit()
            self.db.refresh(issue)
        except Exception:
            self.db.rollback()
            raise
        return issue

    def get_review(self, review_id: str) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_issues(self, review_id: str) -> list[ReviewIssueModel]:
        return self.db.query(ReviewIssueModel).filter(ReviewIssueModel.review_id == review_id).all()

    def get_traces(self, review_id: str) -> list[PipelineTrace]:
        return self.db.query(PipelineTrace).filter(PipelineTrace.review_id == review_id).all()

    def save_trace(self, review_id: str, stage: str, duration_ms: float, input_data: Any, output_data: Any) -> PipelineTrace:
        trace_id = str(uuid.uuid4())
        trace = PipelineTrace(
            id=trace_id,
            review_id=review_id,
            stage=stage,
            duration_ms=duration_ms,
            input_data=input_data if isinstance(input_data, dict) else {},
            output_data=output_data if isinstance(output_data, dict) else {}
        )
        try:
            self.db.add(trace)
            self.db.commit()
            self.db.refresh(trace)
        except Exception:
            self.db.rollback()
            raise
        return trace

    def list_reviews(self, limit: int = 50, offset: int = 0) -> list[Review]:
        return (
            self.db.query(Review)
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_review(self, review_id: str) -> bool:
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if review:
            try:
                self.db.delete(review)
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                raise
        return False
