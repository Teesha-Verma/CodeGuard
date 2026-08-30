import uuid
import logging
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.schemas import ReviewRequest, SnippetReviewRequest, ReviewStatusResponse, ReviewReport, FileReport, ReviewIssue
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
        status="running",
        message="Review pipeline started for PR."
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
        status="running",
        message="Review pipeline started for snippet."
    )


@router.get("/{review_id}", response_model=ReviewReport)
def get_review_status(
    review_id: str,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching review status for {review_id}", extra={"review_id": review_id})

    review = None
    repo_repository = None
    try:
        repo_repository = ReviewRepository(db)
        review = repo_repository.get_review(review_id)
    except Exception as db_err:
        logger.warning(f"Database query failed in get_review_status ({db_err}). Falling back to disk store.")

    store = ReviewStore()
    disk_report = store.get_report(review_id)

    if not review:
        if disk_report:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=disk_report.model_dump())
        raise HTTPException(status_code=404, detail="Review not found.")

    if review.status in ["started", "running"]:
        if disk_report:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=disk_report.model_dump())
        raise HTTPException(status_code=202, detail="Review is still processing.")

    if review.status in ["completed", "timed_out"]:
        if disk_report:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=disk_report.model_dump())
        elif review.status == "timed_out":
            raise HTTPException(status_code=504, detail="Review execution timed out.")
        elif repo_repository:
            # Fallback to DB reconstruction if disk report is not on local filesystem
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

    if review.status == "failed":
        if disk_report:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=disk_report.model_dump())
        raise HTTPException(status_code=500, detail="Review pipeline failed.")

    raise HTTPException(status_code=500, detail=f"Unknown review status: {review.status}")
