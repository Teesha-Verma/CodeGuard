from fastapi import APIRouter
from api.schemas.pipeline import ReviewRequest
from core.pipeline.runner import pipelineRunner
import uuid

router=APIRouter(prefix = "/review" , tags = ["Review"])

@router.post("/")

def submit_review(request:ReviewRequest):
    review_id=str(uuid.uuid4())

    runner = pipelineRunner(
        review_id = review_id,
        repo_url = request.repo_url,
        pr_number= request.pr_number
    )

    diff=runner.run()
    
    return{
        "review id" : review_id,
        "status" : "Diff Extracted",
        "diff preview" : diff[:500]
    }