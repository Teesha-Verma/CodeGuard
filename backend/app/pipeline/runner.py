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
from app.analysis.repository.supporting_context import PRSupportingContextProvider


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

            # Save issues — ALL categories (meaningful + style + suppressed)
            for file_report in file_reports:
                for category, issues_list in [
                    ("meaningful", file_report.meaningful_issues),
                    ("style", file_report.style_findings),
                    ("suppressed", file_report.suppressed_findings),
                ]:
                    for issue in issues_list:
                        try:
                            repo.save_issue(review_id, file_report.file_path, issue, finding_category=category)
                        except Exception as issue_err:
                            logger.debug(f"Could not save {category} issue to DB: {issue_err}")

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
        # Use exact normalized repository-relative paths:
        # Strictly NO basename matching, NO suffix matching, NO substring matching
        primary_diff_files: List[DiffFile] = []
        if pr_changed_files:
            norm_pr_map = {DiffParser.normalize_path(cf): cf for cf in pr_changed_files if cf}
            matched_norm_paths = set()

            for df in all_parsed_diff_files:
                df_norm = DiffParser.normalize_path(df.file_path)
                if df_norm in norm_pr_map:
                    # Skip removed files from primary static analysis
                    if not df.is_deleted:
                        primary_diff_files.append(df)
                    matched_norm_paths.add(df_norm)

            # If any active PR changed file was not captured in unified diff parser, synthesize DiffFile
            for norm_p, orig_p in norm_pr_map.items():
                if norm_p not in matched_norm_paths and norm_p.endswith(".py"):
                    cand_full = os.path.join(repo_dir, norm_p)
                    if os.path.isfile(cand_full):
                        primary_diff_files.append(DiffFile(file_path=orig_p, is_new=False, added_lines=[]))
        else:
            primary_diff_files = [
                df for df in all_parsed_diff_files
                if not df.is_deleted and df.file_path.endswith(".py")
            ]

        # Filter only non-deleted Python files for primary analysis
        primary_py_files = [
            df for df in primary_diff_files
            if not df.is_deleted and df.file_path.endswith(".py")
        ]

        # Step D: Pre-load Scoped Supporting Context (NO repository-wide scanning)
        # PRIMARY ANALYSIS SCOPE = EXACT PR CHANGES
        # REPOSITORY = SUPPORTING CONTEXT ONLY
        repo_intel_start = time.perf_counter()
        context_provider = PRSupportingContextProvider(repo_dir=repo_dir)
        context_bundle = context_provider.resolve_context(primary_diff_files=primary_py_files)
        sources_cache = context_bundle.combined_sources_cache
        repo_intel_map = context_bundle.repo_intelligence
        supporting_files_count = len(context_bundle.supporting_files)
        repo_intel_duration = (time.perf_counter() - repo_intel_start) * 1000

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

        all_traces.append({
            "stage": "repository_supporting_context",
            "duration_ms": repo_intel_duration,
            "input_data": {
                "primary_files": len(primary_py_files),
                "supporting_files": supporting_files_count
            },
            "output_data": {
                "supporting_files_resolved": context_bundle.supporting_files,
                "symbols_count": len(context_bundle.supporting_symbols),
                "architecture_patterns": len(repo_intel_map.get("architecture", [])),
                "hotspots": len(repo_intel_map.get("hotspots", []))
            }
        })

        # Explicit PR scope logging
        logger.info(f"PR Changed Files Detected: {len(pr_changed_files or primary_py_files)}")
        logger.info(f"Primary Files Analyzed: {len(primary_py_files)}")
        logger.info(f"Supporting Context Files: {supporting_files_count}")

        if not primary_py_files:
            logger.warning("No modified Python files found for primary PR review.")

        # Step E: Process Primary PR Files with Deadline Enforcement
        orchestrator = PipelineOrchestrator(review_id=review_id)
        file_reports: List[FileReport] = []
        deadline_exceeded = False
        pr_changed_paths = [df.file_path for df in primary_py_files]

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
                supporting_context=context_bundle.supporting_symbols,
                pr_changed_files=pr_changed_paths,
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
        summary_stats["files_analyzed"] = len(file_reports)
        summary_stats["supporting_files_used"] = supporting_files_count

        # Attach partial review state if deadline was exceeded
        if deadline_exceeded:
            summary_stats["is_partial"] = True
            summary_stats["partial_reason"] = (
                f"Review exceeded maximum duration ({elapsed:.1f}s > {max_duration}s). "
                f"Analyzed {len(file_reports)} of {len(primary_py_files)} primary files."
            )
            summary_stats["processed_files"] = len(file_reports)
            summary_stats["total_files"] = len(primary_py_files)
            summary_stats["remaining_files"] = len(primary_py_files) - len(file_reports)

        # Step G: Create & Persist Review Report (guaranteeing exact PR scope)
        valid_paths_set = {df.file_path for df in primary_py_files}
        pr_scoped_reports = [fr for fr in file_reports if fr.file_path in valid_paths_set]

        review_report = ReviewReport(
            review_id=review_id,
            file_reports=pr_scoped_reports,
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
        final_status = "timed_out" if deadline_exceeded else "completed"
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
