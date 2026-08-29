import os
import shutil
import time
from typing import Dict, Any, List, Optional

from app.db.database import SessionLocal
from app.db.repositories import ReviewRepository
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile, DiffParser
from app.api.schemas import ReviewReport, FileReport, ReviewIssue
from app.storage.review_store import ReviewStore
from app.evaluation.metrics import MetricsCalculator
from app.core.config import get_settings
from app.core.logger import get_logger
from app.analysis.repository.query_engine import RepositoryQueryEngine


def _update_review_status_in_db(review_id: str, status: str) -> bool:
    """Safely update review status using a dedicated short-lived DB session."""
    logger = get_logger("codeguard.pipeline.runner")
    try:
        with SessionLocal() as db:
            repo = ReviewRepository(db)
            repo.update_status(review_id, status)
            return True
    except Exception as e:
        logger.warning(f"Could not update status to {status} in DB for review {review_id}: {e}")
        return False


def _save_review_results_to_db(review_id: str, file_reports: List[FileReport], traces: List[Dict[str, Any]]) -> bool:
    """Safely persist review traces and issues to PostgreSQL using a dedicated short-lived DB session."""
    logger = get_logger("codeguard.pipeline.runner")
    try:
        with SessionLocal() as db:
            repo = ReviewRepository(db)

            # Save traces
            for trace in traces:
                try:
                    repo.save_trace(
                        review_id=review_id,
                        stage=trace.get("stage", "unknown"),
                        duration_ms=trace.get("duration_ms", 0.0),
                        input_data=trace.get("input_data", {}),
                        output_data=trace.get("output_data", {})
                    )
                except Exception as trace_err:
                    logger.debug(f"Could not save trace to DB: {trace_err}")

            # Save issues
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
                        repo.save_issue(review_id, file_report.file_path, issue_data)
                    except Exception as issue_err:
                        logger.debug(f"Could not save issue to DB: {issue_err}")

            return True
    except Exception as e:
        logger.warning(f"Could not save review results to DB for review {review_id}: {e}")
        return False


def run_snippet_review_task(review_id: str, code: str, language: str, filename: str, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for snippet review: {review_id}")

    settings = get_settings()
    _update_review_status_in_db(review_id, "running")

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

        # Build raw issues for summary stats
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

        # Save traces & issues to DB
        _save_review_results_to_db(review_id, [file_report], orchestrator.traces)

        # Mark as completed
        _update_review_status_in_db(review_id, "completed")
        logger.info(f"Snippet review task completed successfully: {review_id}")

    except Exception as e:
        logger.exception(f"Error running snippet review task: {e}")
        _update_review_status_in_db(review_id, "failed")

    finally:
        # Clean up files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_pr_review_task(review_id: str, repo_url: str, pr_number: int, verbose_ast: bool = False):
    logger = get_logger("codeguard.pipeline.runner")
    logger.info(f"Background task started for PR review: {review_id} for {repo_url} #{pr_number}")

    start_time = time.time()
    settings = get_settings()
    max_duration = getattr(settings, "MAX_REVIEW_DURATION_SECONDS", 300)

    # 1. Update review status to "running" in DB
    _update_review_status_in_db(review_id, "running")

    repo_dir = os.path.join(settings.REPOS_DIR, review_id)
    all_traces: List[Dict[str, Any]] = []

    try:
        # Parse owner and repo name from URL
        clean_url = repo_url.rstrip("/").replace(".git", "")
        parts = clean_url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        owner = parts[-2]
        repo_name = parts[-1]

        # Use GitHubClient for authenticated PR metadata, files, diff, and clone
        from app.github import GitHubClient

        github_client = GitHubClient()
        clone_url = repo_url
        base_ref = "main"

        # Step A: GitHub PR Resolution
        pr_res_start = time.perf_counter()
        pr_changed_files: List[str] = []
        try:
            pr_data = github_client.get_pull_request(owner=owner, repo=repo_name, pr_number=pr_number)
            base_ref = pr_data.get("base", {}).get("ref", "main")
            clone_url = pr_data.get("base", {}).get("repo", {}).get("clone_url", repo_url)
        except Exception as api_err:
            logger.warning(f"GitHub API metadata retrieval failed: {api_err}. Proceeding with repo URL.")

        try:
            pr_changed_files = github_client.get_pr_changed_files(owner=owner, repo=repo_name, pr_number=pr_number)
        except Exception as files_err:
            logger.warning(f"GitHub API PR files retrieval failed: {files_err}.")

        pr_res_duration = (time.perf_counter() - pr_res_start) * 1000
        all_traces.append({
            "stage": "github_pr_resolution",
            "duration_ms": pr_res_duration,
            "input_data": {"owner": owner, "repo": repo_name, "pr_number": pr_number},
            "output_data": {
                "clone_url": clone_url,
                "base_ref": base_ref,
                "pr_changed_files_count": len(pr_changed_files)
            }
        })

        # Step B: Clone and checkout PR branch
        clone_start = time.perf_counter()
        checkout_info = github_client.clone_and_checkout_pr(
            repo_url=clone_url,
            pr_number=pr_number,
            target_dir=repo_dir,
            base_ref=base_ref,
        )
        diff_text = checkout_info.get("diff_text", "")
        clone_duration = (time.perf_counter() - clone_start) * 1000
        all_traces.append({
            "stage": "git_clone_and_checkout",
            "duration_ms": clone_duration,
            "input_data": {"target_dir": repo_dir, "base_ref": base_ref},
            "output_data": {"diff_bytes": len(diff_text)}
        })

        # Fallback to GitHub API diff if git local diff was empty
        if not diff_text:
            try:
                diff_text = github_client.get_pull_request_diff(owner=owner, repo=repo_name, pr_number=pr_number)
            except Exception as diff_err:
                logger.warning(f"GitHub API diff retrieval fallback failed: {diff_err}")

        # Step C: Diff Parsing & PR Scope Enforcement
        diff_parse_start = time.perf_counter()
        diff_parser = DiffParser()
        all_parsed_diff_files = diff_parser.parse(diff_text)

        # Distinguish PRIMARY REVIEW FILES from SUPPORTING REPOSITORY CONTEXT
        # If GitHub PR files list is available, scope primary analysis strictly to changed files
        primary_diff_files: List[DiffFile] = []
        if pr_changed_files:
            pr_changed_set = set(pr_changed_files)
            for df in all_parsed_diff_files:
                # Check exact match or relative match
                if df.file_path in pr_changed_set:
                    primary_diff_files.append(df)
                elif any(df.file_path.endswith(cf) or cf.endswith(df.file_path) for cf in pr_changed_files):
                    primary_diff_files.append(df)
            # If no diff files matched directly (e.g. diff_text was from git diff with different prefix), synthesize DiffFiles for pr_changed_files
            if not primary_diff_files:
                for cf in pr_changed_files:
                    if cf.endswith(".py"):
                        primary_diff_files.append(DiffFile(file_path=cf, is_new=False, added_lines=[]))
        else:
            primary_diff_files = [df for df in all_parsed_diff_files if df.file_path.endswith(".py")]

        # Filter only Python files for primary analysis
        primary_py_files = [df for df in primary_diff_files if df.file_path.endswith(".py")]
        supporting_files_count = max(0, len(pr_changed_files) - len(primary_py_files))

        diff_parse_duration = (time.perf_counter() - diff_parse_start) * 1000
        all_traces.append({
            "stage": "diff_parsing_and_scope_filter",
            "duration_ms": diff_parse_duration,
            "input_data": {
                "total_diff_files": len(all_parsed_diff_files),
                "pr_changed_files_count": len(pr_changed_files)
            },
            "output_data": {
                "primary_files_count": len(primary_py_files),
                "supporting_files_count": supporting_files_count
            }
        })

        # Explicit PR scope logging
        logger.info(f"PR changed files: {len(pr_changed_files)}")
        logger.info(f"Primary files analyzed: {len(primary_py_files)}")
        logger.info(f"Supporting context files: {supporting_files_count}")

        if not primary_py_files:
            logger.warning("No modified Python files found for primary PR review.")

        # Step D: Pre-load Repository Source Cache & Pre-compute Repo Intelligence ONCE
        sources_cache: Dict[str, str] = {}
        if os.path.isdir(repo_dir):
            for root, _, files in os.walk(repo_dir):
                for f in files:
                    if f.endswith(".py"):
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, repo_dir).replace("\\", "/")
                        try:
                            with open(full_p, "r", encoding="utf-8") as rf:
                                sources_cache[rel_p] = rf.read()
                        except Exception:
                            pass

        repo_intel_map: Dict[str, Any] = {}
        if sources_cache:
            repo_intel_start = time.perf_counter()
            try:
                changed_paths = [df.file_path for df in primary_py_files]
                query_engine = RepositoryQueryEngine(sources=sources_cache, changed_files=changed_paths)
                repo_intel_map = {
                    "architecture": [a.to_dict() for a in query_engine.find_architecture()],
                    "hotspots": [h.to_dict() for h in query_engine.find_hotspots(top_n=5)],
                    "change_impact": query_engine.find_change_impact().to_dict() if query_engine.find_change_impact() else {},
                }
            except Exception as repo_err:
                logger.warning(f"Pre-computed repository intelligence error: {repo_err}")
            repo_intel_duration = (time.perf_counter() - repo_intel_start) * 1000
            all_traces.append({
                "stage": "repository_intelligence_global",
                "duration_ms": repo_intel_duration,
                "input_data": {"sources_count": len(sources_cache), "changed_files": len(primary_py_files)},
                "output_data": {
                    "architecture_patterns": len(repo_intel_map.get("architecture", [])),
                    "hotspots": len(repo_intel_map.get("hotspots", []))
                }
            })

        # Step E: Process Primary PR Files with Deadline Enforcement
        orchestrator = PipelineOrchestrator(review_id=review_id)
        file_reports: List[FileReport] = []
        deadline_exceeded = False

        for diff_file in primary_py_files:
            # Check deadline before processing each file
            elapsed = time.time() - start_time
            if elapsed > max_duration:
                logger.warning(f"Review {review_id} exceeded maximum duration ({elapsed:.1f}s > {max_duration}s). Finalizing partial report.")
                deadline_exceeded = True
                all_traces.append({
                    "stage": "review_deadline_exceeded",
                    "duration_ms": elapsed * 1000,
                    "input_data": {"max_duration_seconds": max_duration, "processed_files": len(file_reports)},
                    "output_data": {"remaining_files": len(primary_py_files) - len(file_reports)}
                })
                break

            report = orchestrator.process_file(
                diff_file=diff_file,
                repo_path=repo_dir,
                repo_intelligence=repo_intel_map,
                sources_cache=sources_cache,
                verbose_ast=verbose_ast
            )
            file_reports.append(report)

        all_traces.extend(orchestrator.traces)

        # Step F: Calculate summary statistics
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

        # Step G: Create & Persist Review Report
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

        # Save traces & issues to PostgreSQL
        _save_review_results_to_db(review_id, file_reports, all_traces)

        # Step H: Update final status
        final_status = "timed_out" if deadline_exceeded and not file_reports else "completed"
        _update_review_status_in_db(review_id, final_status)
        logger.info(f"PR review task {review_id} finished with status '{final_status}' in {time.time() - start_time:.2f}s")

    except TimeoutError as te:
        logger.error(f"PR review task timed out: {te}")
        _update_review_status_in_db(review_id, "timed_out")

    except Exception as e:
        logger.exception(f"Error running PR review task: {e}")
        _update_review_status_in_db(review_id, "failed")

    finally:
        # Clean up cloned repository files safely
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir, ignore_errors=True)
