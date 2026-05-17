import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.schemas import ReviewRequest, SnippetReviewRequest, ReviewStatusResponse, ReviewReport
from app.core.logger import get_logger
from app.core.config import Settings
from app.api.dependencies import get_app_settings, get_app_logger
import logging

router = APIRouter(prefix="/review", tags=["Review"])

@router.post("/pr", response_model=ReviewStatusResponse)
async def submit_pr_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_app_settings),
    logger: logging.Logger = Depends(get_app_logger)
):
    review_id = str(uuid.uuid4())
    logger.info(f"Received PR review request for {request.repo_url}/pull/{request.pr_number}", extra={"review_id": review_id})
    
    # In a real system, we'd trigger the orchestrator via background tasks or a task queue.
    # For now, we'll just mock the start. The actual orchestrator will be built in Phase 7.
    # background_tasks.add_task(run_pipeline, review_id, request)
    
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
    logger: logging.Logger = Depends(get_app_logger)
):
    review_id = str(uuid.uuid4())
    logger.info(f"Received snippet review request for {request.filename}", extra={"review_id": review_id})
    
    # Background task for snippet review pipeline
    
    return ReviewStatusResponse(
        review_id=review_id,
        status="running",
        message="Review pipeline started for snippet."
    )

@router.get("/{review_id}", response_model=ReviewReport)
async def get_review_status(review_id: str, logger: logging.Logger = Depends(get_app_logger)):
    logger.info(f"Fetching review status for {review_id}", extra={"review_id": review_id})
    # Mocking response until Phase 8 (DB/Storage) is implemented
    raise HTTPException(status_code=404, detail="Review not found or still processing.")
