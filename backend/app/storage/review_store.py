import json
import os
from app.api.schemas import ReviewReport

class ReviewStore:
    """File-based fallback storage for review reports."""
    
    def __init__(self, storage_dir: str = "data/reports"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def save_report(self, report: ReviewReport) -> str:
        file_path = os.path.join(self.storage_dir, f"{report.review_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.json(indent=2))
        return file_path
