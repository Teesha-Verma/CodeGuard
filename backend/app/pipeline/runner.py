import os
import shutil
from typing import Dict, Any, List

from app.db.database import SessionLocal
from app.db.repositories import ReviewRepository
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile
from app.api.schemas import ReviewReport, FileReport, ReviewIssue
from app.storage.review_store import ReviewStore
from app.evaluation.metrics import MetricsCalculator
from app.core.config import get_settings
from app.core.logger import get_logger

def run_snippet_review_task(review_id: str, code: str, language: str, filename: str, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for snippet review: {review_id}")
    
    settings = get_settings()
    db = SessionLocal()
    repo_repository = ReviewRepository(db)
    
    # 1. Update review status to "running"
    repo_repository.update_status(review_id, "running")
    
    temp_dir = os.path.join(settings.REPOS_DIR, f"snippet_{review_id}")
    file_path = os.path.join(temp_dir, filename)
    
    try:
        # Write snippet code to a temp file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Parse diff file (virtual diff where entire file is added)
        lines = code.splitlines()
        diff_file = DiffFile(
            file_path=filename,
            is_new=True,
            added_lines=list(range(1, len(lines) + 1))
        )
        
        # Run orchestrator
        orchestrator = PipelineOrchestrator(review_id=review_id)
        file_report = orchestrator.process_file(diff_file, temp_dir, verbose_ast=verbose_ast)
        
        # Save traces to DB
        for trace in orchestrator.traces:
            repo_repository.save_trace(
                review_id=review_id,
                stage=trace["stage"],
                duration_ms=trace["duration_ms"],
                input_data=trace["input_data"],
                output_data=trace["output_data"]
            )
        
        # Calculate summary statistics
        raw_issues = []
        for issue in file_report.issues:
            raw_issues.append({
                "severity": issue.severity,
                "confidence": issue.confidence,
                "sources": issue.sources
            })
        summary_stats = MetricsCalculator.compute_summary_stats(raw_issues)
        
        # Create review report
        report = ReviewReport(
            review_id=review_id,
            file_reports=[file_report],
            summary_stats=summary_stats,
            evaluation_metrics=None,
            trace_id=review_id
        )
        
        # Save complete report to disk
        store = ReviewStore()
        store.save_report(report)
        
        # Save individual issues to DB
        for issue in file_report.issues:
            issue_data = {
                "line": issue.line,
                "severity": issue.severity,
                "confidence": issue.confidence,
                "issue": issue.issue,
                "root_cause": issue.root_cause,
                "trigger_condition": issue.trigger_condition,
                "fix": issue.fix,
                "patch": issue.patch,
                "issue_type": issue.issue_type,
                "sources": issue.sources,
                "reasoning_trace": issue.reasoning_trace,
                "evidence": issue.evidence
            }
            repo_repository.save_issue(review_id, filename, issue_data)
            
        # Mark as completed
        repo_repository.update_status(review_id, "completed")
        logger.info(f"Snippet review task completed successfully: {review_id}")
        
    except Exception as e:
        logger.exception(f"Error running snippet review task: {e}")
        repo_repository.update_status(review_id, "failed")
        
    finally:
        # Clean up files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        db.close()

def run_pr_review_task(review_id: str, repo_url: str, pr_number: int, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for PR review: {review_id} for {repo_url} #{pr_number}")
    
    settings = get_settings()
    db = SessionLocal()
    repo_repository = ReviewRepository(db)
    
    # 1. Update review status to "running"
    repo_repository.update_status(review_id, "running")
    
    repo_dir = os.path.join(settings.REPOS_DIR, review_id)
    
    try:
        # Parse owner and repo name from URL
        clean_url = repo_url.rstrip("/").replace(".git", "")
        parts = clean_url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Fetch PR info from GitHub API
        headers = {}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
        
        base_ref = "main"
        clone_url = repo_url
        
        try:
            import httpx
            with httpx.Client() as client:
                res = client.get(api_url, headers=headers)
                if res.status_code == 200:
                    pr_data = res.json()
                    base_ref = pr_data.get("base", {}).get("ref", "main")
                    clone_url = pr_data.get("base", {}).get("repo", {}).get("clone_url", repo_url)
                else:
                    logger.warning(f"Failed to fetch PR details from GitHub API: {res.status_code}. Using defaults.")
        except Exception as api_err:
            logger.warning(f"Error calling GitHub API: {api_err}. Using defaults.")
            
        # Add GITHUB_TOKEN authentication to clone URL if needed
        if settings.GITHUB_TOKEN and "github.com" in clone_url:
            authenticated_url = clone_url.replace("https://", f"https://x-access-token:{settings.GITHUB_TOKEN}@")
        else:
            authenticated_url = clone_url
            
        # Clone repo
        import git
        logger.info(f"Cloning repository {clone_url} to {repo_dir}")
        repo = git.Repo.clone_from(authenticated_url, repo_dir)
        
        # Fetch the PR branch
        logger.info(f"Fetching PR #{pr_number}")
        repo.git.fetch("origin", f"pull/{pr_number}/head:pr-{pr_number}")
        repo.git.checkout(f"pr-{pr_number}")
        
        # Get diff text against base branch
        try:
            repo.git.fetch("origin", f"{base_ref}:{base_ref}")
        except Exception:
            pass
            
        logger.info(f"Generating diff against origin/{base_ref}")
        diff_text = repo.git.diff(f"origin/{base_ref}...HEAD")
        
        # Parse diff
        from app.diff.diff_parser import DiffParser
        diff_parser = DiffParser()
        diff_files = diff_parser.parse(diff_text)
        
        if not diff_files:
            logger.warning("No modified files found in diff.")
            
        # Run orchestrator on each file
        orchestrator = PipelineOrchestrator(review_id=review_id)
        file_reports = []
        
        for diff_file in diff_files:
            if diff_file.file_path.endswith(".py"):
                report = orchestrator.process_file(diff_file, repo_dir, verbose_ast=verbose_ast)
                file_reports.append(report)
                
        # Save traces to DB
        for trace in orchestrator.traces:
            repo_repository.save_trace(
                review_id=review_id,
                stage=trace["stage"],
                duration_ms=trace["duration_ms"],
                input_data=trace["input_data"],
                output_data=trace["output_data"]
            )
            
        # Calculate summary statistics
        all_raw_issues = []
        for file_report in file_reports:
            for issue in file_report.issues:
                all_raw_issues.append({
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "sources": issue.sources
                })
                
        summary_stats = MetricsCalculator.compute_summary_stats(all_raw_issues)
        
        # Create review report
        review_report = ReviewReport(
            review_id=review_id,
            file_reports=file_reports,
            summary_stats=summary_stats,
            evaluation_metrics=None,
            trace_id=review_id
        )
        
        # Save complete report to disk
        store = ReviewStore()
        store.save_report(review_report)
        
        # Save individual issues to DB
        for file_report in file_reports:
            for issue in file_report.issues:
                issue_data = {
                    "line": issue.line,
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "issue": issue.issue,
                    "root_cause": issue.root_cause,
                    "trigger_condition": issue.trigger_condition,
                    "fix": issue.fix,
                    "patch": issue.patch,
                    "issue_type": issue.issue_type,
                    "sources": issue.sources,
                    "reasoning_trace": issue.reasoning_trace,
                    "evidence": issue.evidence
                }
                repo_repository.save_issue(review_id, file_report.file_path, issue_data)
                
        # Mark as completed
        repo_repository.update_status(review_id, "completed")
        logger.info(f"PR review task completed successfully: {review_id}")
        
    except Exception as e:
        logger.exception(f"Error running PR review task: {e}")
        repo_repository.update_status(review_id, "failed")
        
    finally:
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir, ignore_errors=True)
        db.close()
