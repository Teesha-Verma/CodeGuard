import uuid
import logging
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.schemas import (
    ReviewRequest,
    SnippetReviewRequest,
    ReviewStatusResponse,
    ReviewReport,
    FileReport,
    ReviewIssue,
    StoredReviewSummary,
    ReviewHistoryResponse,
    DashboardStatsResponse,
    DataflowResponse,
    DataflowNode,
    PlaygroundReviewRequest,
    PlaygroundReviewResponse,
)
from app.evaluation.metrics import MetricsCalculator
from app.core.logger import get_logger
from app.core.config import Settings
from app.api.dependencies import get_app_settings, get_app_logger
from app.db.database import get_db
from app.db.repositories import ReviewRepository
from app.storage.review_store import ReviewStore
from app.pipeline.runner import run_pr_review_task, run_snippet_review_task

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/pr", response_model=ReviewStatusResponse)
async def submit_pr_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_app_settings),
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    review_id = str(uuid.uuid4())
    logger.info(f"Received PR review request for {request.repo_url}/pull/{request.pr_number}", extra={"review_id": review_id})

    # 1. Create a DB record with "started" status if DB available
    try:
        repo_repository = ReviewRepository(db)
        repo_repository.create_review(
            review_id=review_id,
            repo_url=request.repo_url,
            pr_number=request.pr_number
        )
    except Exception as db_err:
        logger.warning(f"Could not create PR review record in DB ({db_err}). Review will proceed with disk storage.")

    # Fast in-memory / local status initialization
    ReviewStore.get_instance().set_review_status(
        review_id=review_id,
        status="queued",
        stage="queued",
        repo_url=request.repo_url,
        pr_number=request.pr_number,
        message="Review pipeline queued for PR."
    )

    # 2. Add pipeline task to background tasks
    background_tasks.add_task(
        run_pr_review_task,
        review_id=review_id,
        repo_url=request.repo_url,
        pr_number=request.pr_number,
        verbose_ast=request.verbose_ast
    )

    return ReviewStatusResponse(
        review_id=review_id,
        status="queued",
        stage="queued",
        message="Review pipeline queued for PR."
    )


@router.post("/snippet", response_model=ReviewStatusResponse)
async def submit_snippet_review(
    request: SnippetReviewRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_app_settings),
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    review_id = str(uuid.uuid4())
    logger.info(f"Received snippet review request for {request.filename}", extra={"review_id": review_id})

    # 1. Create a DB record with "started" status if DB available
    try:
        repo_repository = ReviewRepository(db)
        repo_repository.create_review(
            review_id=review_id,
            repo_url="snippet",
            pr_number=0
        )
    except Exception as db_err:
        logger.warning(f"Could not create snippet review record in DB ({db_err}). Review will proceed with disk storage.")

    # Fast in-memory / local status initialization
    ReviewStore.get_instance().set_review_status(
        review_id=review_id,
        status="queued",
        stage="queued",
        repo_url="snippet",
        pr_number=0,
        message="Review pipeline queued for snippet."
    )

    # 2. Add pipeline task to background tasks
    background_tasks.add_task(
        run_snippet_review_task,
        review_id=review_id,
        code=request.code,
        language=request.language,
        filename=request.filename,
        verbose_ast=request.verbose_ast
    )

    return ReviewStatusResponse(
        review_id=review_id,
        status="queued",
        stage="queued",
        message="Review pipeline queued for snippet."
    )


@router.get("/{review_id}/status", response_model=ReviewStatusResponse)
def get_review_lightweight_status(
    review_id: str,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    """
    Lightweight, high-speed status endpoint (<10ms).
    Retrieves status from in-memory / local fast-cache first, avoiding remote DB latency.
    """
    store = ReviewStore.get_instance()
    status_info = store.get_review_status(review_id)

    if status_info:
        raw_status = status_info.get("status", "running")
        # Normalize to standard statuses
        normalized_status = "processing" if raw_status in ["started", "running"] else raw_status
        return ReviewStatusResponse(
            review_id=review_id,
            status=normalized_status,
            message=status_info.get("message") or f"Review is {normalized_status}.",
            stage=status_info.get("stage"),
            error_code=status_info.get("error_code"),
            error_message=status_info.get("error_message"),
            failed_stage=status_info.get("failed_stage"),
            duration_seconds=status_info.get("duration_seconds"),
            started_at=status_info.get("started_at"),
            updated_at=status_info.get("updated_at"),
            progress_percent=status_info.get("progress_percent")
        )

    # Fallback to DB check only if not found in local cache
    try:
        repo_repository = ReviewRepository(db)
        review = repo_repository.get_review(review_id)
        if review:
            stat = "processing" if review.status in ["started", "running"] else review.status
            return ReviewStatusResponse(
                review_id=review_id,
                status=stat,
                message=f"Review status: {stat}."
            )
    except Exception as db_err:
        logger.warning(f"Database query failed in get_review_lightweight_status: {db_err}")

    raise HTTPException(status_code=404, detail="Review not found.")


@router.get("/{review_id}", response_model=ReviewReport)
def get_review_status(
    review_id: str,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching review report for {review_id}", extra={"review_id": review_id})

    # 1. Fast check for completed report on disk (takes <2ms)
    store = ReviewStore.get_instance()
    disk_report = store.get_report(review_id)
    if disk_report:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=disk_report.model_dump())

    # 2. Fast check in-memory status (<1ms)
    status_info = store.get_review_status(review_id)
    status_val = status_info.get("status") if status_info else None

    # 3. Fallback to DB query only if status not in cache
    review = None
    repo_repository = None
    if not status_val:
        try:
            repo_repository = ReviewRepository(db)
            review = repo_repository.get_review(review_id)
            if review:
                status_val = review.status
        except Exception as db_err:
            logger.warning(f"Database query failed in get_review_status ({db_err}).")

    if not status_val and not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    # 4. Processing / Started: Return HTTP 202 without throwing or heavy work
    if status_val in ["started", "running", "processing", "queued"]:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={
                "review_id": review_id,
                "status": "processing",
                "message": (status_info.get("message") if status_info else None) or "Review is still processing.",
                "stage": (status_info.get("stage") if status_info else None) or "processing"
            }
        )

    # 5. Failed: Return HTTP 200 with failure metadata (NEVER HTTP 500)
    if status_val == "failed":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={
                "review_id": review_id,
                "status": "failed",
                "error_code": (status_info.get("error_code") if status_info else None) or "PIPELINE_STAGE_FAILED",
                "error_message": (status_info.get("error_message") if status_info else None) or "Review pipeline failed during execution.",
                "failed_stage": (status_info.get("failed_stage") if status_info else None) or "unknown",
                "duration_seconds": (status_info.get("duration_seconds") if status_info else None) or 0.0
            }
        )

    # 6. Timed Out
    if status_val == "timed_out":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={
                "review_id": review_id,
                "status": "timed_out",
                "error_code": "REVIEW_DEADLINE_EXCEEDED",
                "error_message": "Review execution timed out."
            }
        )

    # 7. Completed: Attempt DB reconstruction if disk report is absent
    if status_val == "completed":
        if not repo_repository:
            try:
                repo_repository = ReviewRepository(db)
            except Exception:
                pass

        if repo_repository:
            try:
                db_issues = repo_repository.get_issues(review_id)
                issues_by_file: Dict[str, list] = {}
                for dbi in db_issues:
                    evidence = dbi.evidence or {}
                    issue_obj = ReviewIssue(
                        line=dbi.line_number or 1,
                        severity=dbi.severity or "medium",
                        confidence=dbi.confidence or 0.8,
                        issue=dbi.issue_description or "",
                        root_cause=dbi.root_cause or "",
                        trigger_condition=dbi.trigger_condition or "",
                        fix=dbi.fix_suggestion or "",
                        patch=dbi.patch,
                        issue_type=dbi.issue_type or "code_smell",
                        sources=dbi.sources or ["ast"],
                        reasoning_trace=dbi.reasoning_trace or [],
                        evidence=evidence,
                        signal_priority=evidence.get("signal_priority", "medium"),
                        issue_category=evidence.get("issue_category", "runtime logic risks"),
                        is_low_signal=evidence.get("is_low_signal", False),
                        detection_source=evidence.get("detection_source", "ast"),
                        reasoning_source=evidence.get("reasoning_source", "static_analysis"),
                        priority_score=evidence.get("priority_score", 0.50),
                        detection_sources=evidence.get("detection_sources", ["ast"]),
                    )
                    issues_by_file.setdefault(dbi.file_path, []).append(issue_obj)

                file_reports = [FileReport(file_path=fp, issues=issues) for fp, issues in issues_by_file.items()]
                all_raw_issues = [
                    {
                        "severity": i.severity,
                        "confidence": i.confidence,
                        "sources": i.sources,
                        "is_low_signal": i.is_low_signal,
                        "detection_sources": i.detection_sources,
                        "reasoning_source": i.reasoning_source
                    }
                    for fr in file_reports for i in (fr.meaningful_issues + fr.style_findings + fr.suppressed_findings)
                ]
                summary_stats = MetricsCalculator.compute_summary_stats(all_raw_issues)
                reconstructed = ReviewReport(
                    review_id=review_id,
                    file_reports=file_reports,
                    summary_stats=summary_stats,
                    evaluation_metrics=None,
                    trace_id=review_id
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(content=reconstructed.model_dump())
            except Exception as recon_err:
                logger.warning(f"Failed to reconstruct review report from DB: {recon_err}")
                raise HTTPException(status_code=404, detail="Review report file not found on disk.")
        else:
            raise HTTPException(status_code=404, detail="Review report file not found on disk.")

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=200,
        content={"review_id": review_id, "status": status_val, "message": f"Review status: {status_val}"}
    )


@router.get("", response_model=ReviewHistoryResponse)
@router.get("/history", response_model=ReviewHistoryResponse)
def list_review_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: Optional[str] = None,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    """
    Returns paginated review history from disk storage (or database)
    for review history and dashboard displays.
    """
    store = ReviewStore()
    summaries, total = store.list_reports(limit=limit, offset=offset, status=status, search=search)
    return ReviewHistoryResponse(
        reviews=summaries,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/summary/stats", response_model=DashboardStatsResponse)
def get_dashboard_summary_stats(
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    """
    Returns real aggregated dashboard KPI metrics computed across persisted reviews.
    """
    store = ReviewStore()
    all_summaries, total = store.list_reports(limit=500, offset=0)

    completed = [r for r in all_summaries if r.status == "completed"]
    total_issues = sum(r.total_issues for r in completed)
    critical_high = sum(r.critical_issues + r.high_issues for r in completed)

    return DashboardStatsResponse(
        total_reviews=len(all_summaries),
        completed_reviews=len(completed),
        total_issues_found=total_issues,
        total_issues=total_issues,
        critical_high_issues=critical_high,
        critical_count=sum(r.critical_issues for r in completed),
        recent_reviews=all_summaries[:10]
    )


@router.delete("/{review_id}")
def delete_review(
    review_id: str,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    """Deletes a review record from database and disk store."""
    store = ReviewStore()
    disk_deleted = store.delete_report(review_id)

    db_deleted = False
    try:
        repo = ReviewRepository(db)
        db_deleted = repo.delete_review(review_id)
    except Exception as e:
        logger.warning(f"Could not delete review {review_id} from DB: {e}")

    if not disk_deleted and not db_deleted:
        raise HTTPException(status_code=404, detail="Review not found.")

    return {"status": "deleted", "review_id": review_id}


@router.get("/{review_id}/findings/{line}/dataflow", response_model=DataflowResponse)
def get_finding_dataflow(
    review_id: str,
    line: int,
    logger: logging.Logger = Depends(get_app_logger),
):
    """
    Extracts deterministic source-to-sink taint propagation path for a finding at target line.
    Uses existing analysis results without rerunning analysis.
    """
    store = ReviewStore()
    report = store.get_report(review_id)
    if not report:
        raise HTTPException(status_code=404, detail="Review not found.")

    target_issue: Optional[ReviewIssue] = None
    target_file = ""

    for file_rep in report.file_reports:
        for iss in file_rep.meaningful_issues + file_rep.style_findings:
            if iss.line == line:
                target_issue = iss
                target_file = file_rep.file_path
                break
        if target_issue:
            break

    if not target_issue:
        # Fallback: search closest line in any file
        for file_rep in report.file_reports:
            if file_rep.meaningful_issues:
                target_issue = file_rep.meaningful_issues[0]
                target_file = file_rep.file_path
                break

    if not target_issue:
        return DataflowResponse(
            review_id=review_id,
            file_path="",
            line=line,
            has_dataflow=False,
            nodes=[],
            message="No finding found at specified line."
        )

    raw_path = target_issue.dataflow_path or []
    if not raw_path:
        # Check evidence for dataflow findings
        df_findings = target_issue.evidence.get("dataflow_findings", [])
        if df_findings and isinstance(df_findings, list) and isinstance(df_findings[0], dict):
            raw_path = [str(p) for p in df_findings[0].get("flow_path", [])]

    if not raw_path:
        return DataflowResponse(
            review_id=review_id,
            file_path=target_file,
            line=target_issue.line,
            has_dataflow=False,
            nodes=[],
            message="This finding was identified via structural AST pattern rules rather than an interprocedural taint trace."
        )

    nodes: List[DataflowNode] = []
    for idx, step in enumerate(raw_path):
        role = "PROPAGATION"
        desc = "Data propagates through internal variable reference."
        if idx == 0:
            role = "SOURCE"
            desc = "Untrusted input enters the application boundary."
        elif idx == 1:
            role = "INPUT"
            desc = "External value is assigned to a local variable without sanitization."
        elif idx == len(raw_path) - 1:
            role = "SINK"
            desc = "Tainted value reaches sensitive execution sink."
        elif any(k in step for k in ["format", 'f"', "concat", "+"]):
            role = "TRANSFORMATION"
            desc = "String interpolation incorporates untrusted value into execution buffer."

        nodes.append(DataflowNode(
            id=f"node-{idx}",
            step_number=idx + 1,
            label=step,
            role=role,
            description=desc,
            code_snippet=step,
            line=target_issue.line,
            file_path=target_file
        ))

    return DataflowResponse(
        review_id=review_id,
        file_path=target_file,
        line=target_issue.line,
        has_dataflow=True,
        nodes=nodes,
        message=None
    )


@router.post("/playground", response_model=PlaygroundReviewResponse)
def analyze_playground_code(
    request: PlaygroundReviewRequest,
    settings: Settings = Depends(get_app_settings),
    logger: logging.Logger = Depends(get_app_logger),
):
    """
    Re-analyzes modified source code in Fix Playground using CodeGuard's
    deterministic static analysis, AST visitor, and taint engines.
    """
    import os
    import shutil
    from app.diff.diff_parser import DiffFile
    from app.pipeline.orchestrator import PipelineOrchestrator

    playground_id = f"pg_{uuid.uuid4().hex[:8]}"
    temp_dir = os.path.join(settings.REPOS_DIR, playground_id)
    filename = request.filename or "snippet.py"
    file_path = os.path.join(temp_dir, filename)

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.code)

        lines = request.code.splitlines()
        diff_file = DiffFile(
            file_path=filename,
            is_new=True,
            added_lines=list(range(1, len(lines) + 1))
        )

        orchestrator = PipelineOrchestrator(review_id=playground_id)
        file_report = orchestrator.process_file(diff_file, temp_dir, verbose_ast=False)

        raw_issues = []
        for issue in file_report.issues:
            raw_issues.append({
                "severity": issue.severity,
                "confidence": issue.confidence,
                "sources": issue.sources,
                "is_low_signal": getattr(issue, "is_low_signal", False),
                "detection_sources": getattr(issue, "detection_sources", issue.sources),
                "reasoning_source": getattr(issue, "reasoning_source", "static_analysis")
            })
        summary_stats = MetricsCalculator.compute_summary_stats(raw_issues)

        target_cat = (request.original_issue_category or "").lower()
        target_line = getattr(request, "original_finding_line", None) or getattr(request, "original_issue_line", None)

        security_issues = [
            i for i in file_report.issues
            if (getattr(i, "issue_type", "") == "security" and i.severity in ("critical", "high"))
            or (i.severity == "critical")
            or "injection" in i.issue.lower()
            or "command" in i.issue.lower()
            or "subprocess" in i.issue.lower()
            or "pickle" in i.issue.lower()
            or "deserialization" in i.issue.lower()
            or "traversal" in i.issue.lower()
        ]

        if target_cat:
            matching = [
                i for i in security_issues
                if target_cat in (getattr(i, "category", "") or "").lower()
                or target_cat in (getattr(i, "issue_type", "") or "").lower()
                or target_cat in i.issue.lower()
            ]
            is_unresolved = bool(matching)
        elif target_line:
            matching = [
                i for i in security_issues
                if abs(i.line - target_line) <= 2 or len(lines) <= 15
            ]
            is_unresolved = bool(matching)
        else:
            is_unresolved = bool(security_issues)

        if is_unresolved:
            resolved = False
            count = len(security_issues)
            message = f"Issue Still Detected: CodeGuard identified {count} security risk(s) remaining in the code."
            status = "still_detected"
        else:
            resolved = True
            message = "Issue Resolved: Deterministic AST & taint analysis confirms the vulnerability pattern is eliminated."
            status = "resolved"

        return PlaygroundReviewResponse(
            status=status,
            resolved=resolved,
            is_resolved=resolved,
            total_issues=len(file_report.issues),
            message=message,
            findings=file_report.issues,
            summary_stats=summary_stats,
        )
    except Exception as err:
        logger.warning(f"Playground analysis failed: {err}")
        return PlaygroundReviewResponse(
            status="error",
            resolved=False,
            message=f"Analysis failed: {str(err)}",
            findings=[],
            summary_stats={},
        )
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

