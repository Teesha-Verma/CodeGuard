import os
import shutil
from typing import Dict, Any, List, Optional

from app.db.database import SessionLocal
from app.db.repositories import ReviewRepository
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile
from app.api.schemas import ReviewReport, FileReport, ReviewIssue
from app.storage.review_store import ReviewStore
from app.evaluation.metrics import MetricsCalculator
from app.core.config import get_settings
from app.core.logger import get_logger


def _get_safe_repo_repository():
    """Attempt to create database session and repository; return (db, repo_repo) or (None, None)."""
    logger = get_logger("codeguard.pipeline.runner")
    try:
        db = SessionLocal()
        # Test basic connection with a ping or instantiation
        repo = ReviewRepository(db)
        return db, repo
    except Exception as e:
        logger.warning(f"PostgreSQL session not available ({e}). Review will proceed with disk storage.")
        return None, None


def run_snippet_review_task(review_id: str, code: str, language: str, filename: str, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for snippet review: {review_id}")

    settings = get_settings()
    db, repo_repository = _get_safe_repo_repository()

    # 1. Update review status to "running" if DB is available
    if repo_repository:
        try:
            repo_repository.update_status(review_id, "running")
        except Exception as e:
            logger.warning(f"Could not update status to running in DB: {e}")

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

        # Save traces to DB if available
        if repo_repository:
            for trace in orchestrator.traces:
                try:
                    repo_repository.save_trace(
                        review_id=review_id,
                        stage=trace["stage"],
                        duration_ms=trace["duration_ms"],
                        input_data=trace["input_data"],
                        output_data=trace["output_data"]
                    )
                except Exception as trace_err:
                    logger.debug(f"Could not save trace to DB: {trace_err}")

        raw_issues = []
        all_report_issues = file_report.meaningful_issues + file_report.style_findings + file_report.suppressed_findings
        for issue in all_report_issues:
            raw_issues.append({
                "severity": issue.severity,
                "confidence": issue.confidence,
                "sources": issue.sources,
                "is_low_signal": issue.is_low_signal,
                "detection_sources": issue.detection_sources,
                "reasoning_source": issue.reasoning_source
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

        # Save individual issues to DB if available
        if repo_repository:
            for issue in file_report.meaningful_issues:
                try:
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
                except Exception as issue_err:
                    logger.debug(f"Could not save issue to DB: {issue_err}")

            # Mark as completed
            try:
                repo_repository.update_status(review_id, "completed")
            except Exception as status_err:
                logger.debug(f"Could not update status to completed in DB: {status_err}")

        logger.info(f"Snippet review task completed successfully: {review_id}")

    except Exception as e:
        logger.exception(f"Error running snippet review task: {e}")
        if repo_repository:
            try:
                repo_repository.update_status(review_id, "failed")
            except Exception:
                pass

    finally:
        # Clean up files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        if db is not None:
            try:
                db.close()
            except Exception:
                pass


def run_pr_review_task(review_id: str, repo_url: str, pr_number: int, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for PR review: {review_id} for {repo_url} #{pr_number}")

    settings = get_settings()
    db, repo_repository = _get_safe_repo_repository()

    # 1. Update review status to "running" if DB available
    if repo_repository:
        try:
            repo_repository.update_status(review_id, "running")
        except Exception as e:
            logger.warning(f"Could not update status to running in DB: {e}")

    repo_dir = os.path.join(settings.REPOS_DIR, review_id)

    try:
        # Parse owner and repo name from URL
        clean_url = repo_url.rstrip("/").replace(".git", "")
        parts = clean_url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        owner = parts[-2]
        repo_name = parts[-1]

        # Use GitHubClient for authenticated PR metadata, clone, and checkout
        from app.github import GitHubClient
        from app.diff.diff_parser import DiffParser

        github_client = GitHubClient()
        clone_url = repo_url
        base_ref = "main"

        try:
            pr_data = github_client.get_pull_request(owner=owner, repo=repo_name, pr_number=pr_number)
            base_ref = pr_data.get("base", {}).get("ref", "main")
            clone_url = pr_data.get("base", {}).get("repo", {}).get("clone_url", repo_url)
        except Exception as api_err:
            logger.warning(f"GitHub API metadata retrieval failed: {api_err}. Proceeding with repo URL.")

        # Clone and checkout PR branch
        checkout_info = github_client.clone_and_checkout_pr(
            repo_url=clone_url,
            pr_number=pr_number,
            target_dir=repo_dir,
            base_ref=base_ref,
        )
        diff_text = checkout_info.get("diff_text", "")

        # Fallback to GitHub API diff if git local diff was empty
        if not diff_text:
            try:
                diff_text = github_client.get_pull_request_diff(owner=owner, repo=repo_name, pr_number=pr_number)
            except Exception as diff_err:
                logger.warning(f"GitHub API diff retrieval fallback failed: {diff_err}")

        # Parse diff
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

        # Save traces to DB if available
        if repo_repository:
            runner_traces = [
                {
                    "stage": "github_pr_resolution",
                    "duration_ms": 50.0,
                    "input_data": {"owner": owner, "repo": repo_name, "pr_number": pr_number},
                    "output_data": {"clone_url": clone_url, "base_ref": base_ref}
                },
                {
                    "stage": "diff_parsing",
                    "duration_ms": 10.0,
                    "input_data": {"diff_bytes": len(diff_text)},
                    "output_data": {"files_count": len(diff_files)}
                }
            ]
            for trace in runner_traces + orchestrator.traces:
                try:
                    repo_repository.save_trace(
                        review_id=review_id,
                        stage=trace["stage"],
                        duration_ms=trace["duration_ms"],
                        input_data=trace["input_data"],
                        output_data=trace["output_data"]
                    )
                except Exception as trace_err:
                    logger.debug(f"Could not save trace to DB: {trace_err}")

        # Calculate summary statistics
        all_raw_issues = []
        for file_report in file_reports:
            all_report_issues = file_report.meaningful_issues + file_report.style_findings + file_report.suppressed_findings
            for issue in all_report_issues:
                all_raw_issues.append({
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "sources": issue.sources,
                    "is_low_signal": issue.is_low_signal,
                    "detection_sources": issue.detection_sources,
                    "reasoning_source": issue.reasoning_source
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

        # Save individual issues to DB if available
        if repo_repository:
            for file_report in file_reports:
                for issue in file_report.meaningful_issues:
                    try:
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
                    except Exception as issue_err:
                        logger.debug(f"Could not save issue to DB: {issue_err}")

            # Mark as completed
            try:
                repo_repository.update_status(review_id, "completed")
            except Exception as status_err:
                logger.debug(f"Could not update status to completed in DB: {status_err}")

        logger.info(f"PR review task completed successfully: {review_id}")

    except Exception as e:
        logger.exception(f"Error running PR review task: {e}")
        if repo_repository:
            try:
                repo_repository.update_status(review_id, "failed")
            except Exception:
                pass

    finally:
        # Clean up files
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir, ignore_errors=True)
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
