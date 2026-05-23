from sqlalchemy.orm import Session
from app.db.models import PipelineTrace
import uuid

class TraceStore:
    """High-level abstraction for saving pipeline stage traces for observability."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def log_trace(self, review_id: str, stage: str, duration_ms: float, input_data: dict = None, output_data: dict = None):
        trace = PipelineTrace(
            id=str(uuid.uuid4()),
            review_id=review_id,
            stage=stage,
            duration_ms=duration_ms,
            input_data=input_data,
            output_data=output_data
        )
        self.db.add(trace)
        self.db.commit()
