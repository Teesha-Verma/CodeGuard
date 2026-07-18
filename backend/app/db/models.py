from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, index=True)
    repo_url = Column(String, index=True)
    pr_number = Column(Integer, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    issues = relationship("ReviewIssueModel", back_populates="review", cascade="all, delete-orphan")
    traces = relationship("PipelineTrace", back_populates="review", cascade="all, delete-orphan")

class ReviewIssueModel(Base):
    __tablename__ = "review_issues"
    
    id = Column(String, primary_key=True, index=True)
    review_id = Column(String, ForeignKey("reviews.id"))
    file_path = Column(String, index=True)
    line_number = Column(Integer)
    severity = Column(String)
    confidence = Column(Float)
    issue_description = Column(String)
    root_cause = Column(String)
    trigger_condition = Column(String)
    fix_suggestion = Column(String)
    patch = Column(String, nullable=True)
    issue_type = Column(String)
    
    # PostgreSQL JSONB fields for V1 output structures
    sources = Column(JSONB, nullable=True)
    reasoning_trace = Column(JSONB, nullable=True)
    evidence = Column(JSONB, nullable=True)
    
    review = relationship("Review", back_populates="issues")

class PipelineTrace(Base):
    __tablename__ = "pipeline_traces"
    
    id = Column(String, primary_key=True, index=True)
    review_id = Column(String, ForeignKey("reviews.id"))
    stage = Column(String)
    duration_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    
    review = relationship("Review", back_populates="traces")
