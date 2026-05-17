from sqlalchemy.orm import Session
from app.db.models import ReviewIssueModel
from app.core.logger import PipelineLogger

class FalsePositiveTracker:
    """Tracks user feedback on false positive issues for future LLM fine-tuning."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = PipelineLogger(review_id="system", stage="eval")
        
    def mark_false_positive(self, issue_id: str, feedback: str):
        issue = self.db.query(ReviewIssueModel).filter(ReviewIssueModel.id == issue_id).first()
        if issue:
            self.logger.info(f"Marking issue {issue_id} as false positive. Feedback: {feedback}")
            # Mock: In a real system, we update a boolean field or separate feedback table.
            return True
        return False
