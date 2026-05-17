from sqlalchemy.orm import Session
from app.db.models import Review, ReviewIssueModel, PipelineTrace
import uuid

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
        issue = ReviewIssueModel(
            id=issue_id,
            review_id=review_id,
            file_path=file_path,
            line_number=issue_data.get("line"),
            severity=issue_data.get("severity"),
            confidence=issue_data.get("confidence"),
            issue_description=issue_data.get("issue"),
            root_cause=issue_data.get("root_cause"),
            fix_suggestion=issue_data.get("fix"),
            patch=issue_data.get("patch"),
            issue_type=issue_data.get("issue_type"),
            source=issue_data.get("source")
        )
        self.db.add(issue)
        self.db.commit()
