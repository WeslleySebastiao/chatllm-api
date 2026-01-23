from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.models.reviews.reviews_schemas import PRReviewRunRequest, PRReviewRunResponse
from src.services.reviews.pipeline.graph import build_review_graph
from src.core.config import *


router_review = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

graph = build_review_graph()

def _require_api_key(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if token != Settings.API_KEY:
        raise HTTPException(status_code=401, detail="Authorization Bearer token do not match")


@router_review.post("/pr/run", response_model=PRReviewRunResponse)
async def pr_run(
    payload: PRReviewRunRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_github_token: str | None = Header(default=None, alias="X-GitHub-Token"),
):

    token = credentials.credentials
    if token != Settings.API_KEY:
        raise HTTPException(status_code=401, detail="Authorization Bearer token do not match")
    
    if not x_github_token:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Token header")

    initial_state = {
        "github_token": x_github_token,
        "repo_full_name": payload.repo_full_name,
        "pr_number": payload.pr_number,
        "head_sha": payload.head_sha,
        "base_sha": payload.base_sha,
        "user_id": "github-actions",
        "errors": [],
    }

    final_state = await graph.ainvoke(initial_state)

    return PRReviewRunResponse(
        repo_full_name=payload.repo_full_name,
        pr_number=payload.pr_number,
        head_sha=payload.head_sha,
        result=final_state.get("final_report", {}),
    )
