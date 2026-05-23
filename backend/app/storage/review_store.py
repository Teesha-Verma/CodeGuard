import json
import os
from typing import Optional
from app.api.schemas import ReviewReport

class ReviewStore:
    """File-based fallback storage for review reports."""
    
    def __init__(self, storage_dir: str = "data/reports"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def save_report(self, report: ReviewReport) -> str:
        file_path = os.path.join(self.storage_dir, f"{report.review_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        return file_path

    def get_report(self, review_id: str) -> Optional[ReviewReport]:
        file_path = os.path.join(self.storage_dir, f"{review_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ReviewReport.parse_obj(data)
