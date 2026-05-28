import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.schemas import ReviewRequest, SnippetReviewRequest, ReviewStatusResponse, ReviewReport
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
    
    # 1. Create a DB record with "started" status
    repo_repository = ReviewRepository(db)
    repo_repository.create_review(
        review_id=review_id,
        repo_url=request.repo_url,
        pr_number=request.pr_number
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
    
    # 1. Create a DB record with "started" status
    repo_repository = ReviewRepository(db)
    repo_repository.create_review(
        review_id=review_id,
        repo_url="snippet",
        pr_number=0
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
        status="running",
        message="Review pipeline started for snippet."
    )

@router.get("/{review_id}", response_model=ReviewReport)
async def get_review_status(
    review_id: str,
    logger: logging.Logger = Depends(get_app_logger),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching review status for {review_id}", extra={"review_id": review_id})
    
    repo_repository = ReviewRepository(db)
    review = repo_repository.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
        
    if review.status in ["started", "running"]:
        raise HTTPException(status_code=202, detail="Review is still processing.")
        
    if review.status == "failed":
        raise HTTPException(status_code=500, detail="Review pipeline failed.")
        
    if review.status == "completed":
        store = ReviewStore()
        report = store.get_report(review_id)
        if report:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=report.model_dump())
        else:
            raise HTTPException(status_code=404, detail="Review report file not found on disk.")
            
    raise HTTPException(status_code=500, detail=f"Unknown review status: {review.status}")
