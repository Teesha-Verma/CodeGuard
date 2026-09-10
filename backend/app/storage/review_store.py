import json
import os
import glob
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from app.api.schemas import ReviewReport, StoredReviewSummary

class ReviewStore:
    """File-based fallback storage for review reports with in-memory status cache."""
    _instance: Optional["ReviewStore"] = None
    _active_status: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls, storage_dir: str = "data/reports") -> "ReviewStore":
        if cls._instance is None:
            cls._instance = cls(storage_dir=storage_dir)
        return cls._instance

    def __init__(self, storage_dir: str = "data/reports"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def set_review_status(
        self,
        review_id: str,
        status: str,
        stage: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        failed_stage: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        repo_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        message: Optional[str] = None,
        progress_percent: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Sets review status in in-memory cache and writes a lightweight status file."""
        now_iso = datetime.now(timezone.utc).isoformat()
        current = self._active_status.get(review_id, {})
        started_at = current.get("started_at") or now_iso

        status_data: Dict[str, Any] = {
            "review_id": review_id,
            "status": status,
            "stage": stage or current.get("stage"),
            "error_code": error_code or current.get("error_code"),
            "error_message": error_message or current.get("error_message"),
            "failed_stage": failed_stage or current.get("failed_stage"),
            "duration_seconds": duration_seconds if duration_seconds is not None else current.get("duration_seconds"),
            "repo_url": repo_url or current.get("repo_url"),
            "pr_number": pr_number or current.get("pr_number"),
            "message": message or current.get("message") or f"Review is {status}",
            "progress_percent": progress_percent if progress_percent is not None else current.get("progress_percent"),
            "started_at": started_at,
            "updated_at": now_iso,
        }

        self._active_status[review_id] = status_data

        # Persist lightweight status file asynchronously or directly
        try:
            status_file = os.path.join(self.storage_dir, f"{review_id}_status.json")
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
        except Exception:
            pass

        return status_data

    def get_review_status(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Fast status retrieval: memory first (<1ms), status file second (<2ms), report file third (<3ms)."""
        # 1. Fast in-memory cache
        if review_id in self._active_status:
            return self._active_status[review_id]

        # 2. Check lightweight status file
        status_file = os.path.join(self.storage_dir, f"{review_id}_status.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._active_status[review_id] = data
                    return data
            except Exception:
                pass

        # 3. Check full report file
        report_file = os.path.join(self.storage_dir, f"{review_id}.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    status = "failed" if "error" in data or "error_message" in data else "completed"
                    status_data = {
                        "review_id": review_id,
                        "status": status,
                        "stage": "completed" if status == "completed" else "failed",
                        "error_code": data.get("error_code"),
                        "error_message": data.get("error_message"),
                        "failed_stage": data.get("failed_stage"),
                        "duration_seconds": data.get("duration_seconds", 0.0),
                        "repo_url": data.get("repo_url"),
                        "pr_number": data.get("pr_number"),
                        "message": "Review completed successfully." if status == "completed" else "Review pipeline failed.",
                        "progress_percent": 100 if status == "completed" else None,
                        "started_at": data.get("created_at"),
                        "updated_at": data.get("created_at"),
                    }
                    self._active_status[review_id] = status_data
                    return status_data
            except Exception:
                pass

        return None
        
    def save_report(self, report: ReviewReport) -> str:
        file_path = os.path.join(self.storage_dir, f"{report.review_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        
        # Update in-memory status
        self.set_review_status(
            review_id=report.review_id,
            status="completed",
            stage="completed",
            duration_seconds=report.duration_seconds,
            repo_url=report.repo_url,
            pr_number=report.pr_number,
            message="Review completed successfully.",
            progress_percent=100
        )
        return file_path

    def get_report(self, review_id: str) -> Optional[ReviewReport]:
        file_path = os.path.join(self.storage_dir, f"{review_id}.json")
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ReviewReport.model_validate(data)
        except Exception:
            return None

    def delete_report(self, review_id: str) -> bool:
        deleted = False
        file_path = os.path.join(self.storage_dir, f"{review_id}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted = True
            except OSError:
                pass

        status_path = os.path.join(self.storage_dir, f"{review_id}_status.json")
        if os.path.exists(status_path):
            try:
                os.remove(status_path)
                deleted = True
            except OSError:
                pass

        self._active_status.pop(review_id, None)
        return deleted

    def list_reports(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[StoredReviewSummary], int]:
        """Lists persisted review summaries with pagination and search filtering."""
        all_json = glob.glob(os.path.join(self.storage_dir, "*.json"))
        # Exclude temporary status files from reports listing
        files = [f for f in all_json if not f.endswith("_status.json")]
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

        summaries: List[StoredReviewSummary] = []
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                rev_id = data.get("review_id") or os.path.splitext(os.path.basename(file_path))[0]
                repo_url = data.get("repo_url")
                pr_num = data.get("pr_number")
                filename = data.get("snippet_filename")
                file_reports = data.get("file_reports", [])
                if not filename and file_reports:
                    filename = file_reports[0].get("file_path", "snippet.py")

                is_snippet = not repo_url or repo_url == "snippet"
                rev_type = "snippet" if is_snippet else "pr"
                
                report_status = "completed"
                if "error" in data:
                    report_status = "failed"

                if status and status != "all" and report_status != status:
                    continue

                if search:
                    s_lower = search.lower()
                    target_str = f"{repo_url or ''} {pr_num or ''} {filename or ''} {rev_id}".lower()
                    if s_lower not in target_str:
                        continue

                stats = data.get("summary_stats", {})
                by_sev = stats.get("by_severity", {})

                created_at = data.get("created_at")
                if not created_at:
                    mtime = os.path.getmtime(file_path)
                    created_at = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

                summary = StoredReviewSummary(
                    review_id=rev_id,
                    type=rev_type,
                    repo_url=repo_url,
                    pr_number=pr_num,
                    filename=filename,
                    language="python",
                    status=report_status,
                    created_at=created_at,
                    duration_seconds=data.get("duration_seconds", 25.0),
                    total_issues=stats.get("total_issues", 0),
                    meaningful_issues=stats.get("meaningful_issues", stats.get("total_issues", 0)),
                    style_findings=stats.get("style_findings", 0),
                    suppressed_findings=stats.get("suppressed_findings", 0),
                    critical_issues=by_sev.get("critical", 0),
                    high_issues=by_sev.get("high", 0),
                    error_message=data.get("error_message")
                )
                summaries.append(summary)
            except Exception:
                continue

        total = len(summaries)
        paginated = summaries[offset : offset + limit]
        return paginated, total
