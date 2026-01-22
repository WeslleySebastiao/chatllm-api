from pydantic import BaseModel

class PRReviewRunRequest(BaseModel):
    repo_full_name: str
    pr_number: int
    head_sha: str
    base_sha: str

class PRReviewRunResponse(BaseModel):
    repo_full_name: str
    pr_number: int
    head_sha: str
    result: dict
