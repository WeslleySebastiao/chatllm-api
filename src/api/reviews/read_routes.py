from fastapi import APIRouter, HTTPException, Query
from src.data.supaBase.supaBase_pr_review_read_db import SupaBasePRReviewReadDB

router_reviews_read = APIRouter(prefix="/api/v1/reviews", tags=["reviews-read"])


@router_reviews_read.get("/pr/latest")
def get_latest_review(
    repo_full_name: str = Query(..., description="Ex: WeslleySebastiao/chatllm-api"),
    pr_number: int = Query(..., description="Número do PR"),
):
    job = SupaBasePRReviewReadDB.get_latest_job(repo_full_name, pr_number)
    if not job:
        raise HTTPException(status_code=404, detail="No review job found for this PR")

    report = SupaBasePRReviewReadDB.get_report_by_job(job["id"])
    if not report:
        # job pode existir mas ainda não terminou
        return {
            "job": job,
            "report": None,
            "counts": {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "NIT": 0},
            "findings": [],
            "tests_suggested": [],
        }

    findings = SupaBasePRReviewReadDB.get_findings(report["id"])
    tests = SupaBasePRReviewReadDB.get_test_suggestions(report["id"])
    counts = SupaBasePRReviewReadDB.get_counts_by_severity(report["id"])

    return {
        "job": job,
        "report": report,
        "counts": counts,
        "findings": findings,
        "tests_suggested": [t["suggestion"] for t in tests],
    }


@router_reviews_read.get("/jobs/{job_id}")
def get_review_by_job(job_id: str):
    job = SupaBasePRReviewReadDB.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    report = SupaBasePRReviewReadDB.get_report_by_job(job_id)
    if not report:
        return {
            "job": job,
            "report": None,
            "counts": {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "NIT": 0},
            "findings": [],
            "tests_suggested": [],
        }

    findings = SupaBasePRReviewReadDB.get_findings(report["id"])
    tests = SupaBasePRReviewReadDB.get_test_suggestions(report["id"])
    counts = SupaBasePRReviewReadDB.get_counts_by_severity(report["id"])

    return {
        "job": job,
        "report": report,
        "counts": counts,
        "findings": findings,
        "tests_suggested": [t["suggestion"] for t in tests],
    }


@router_reviews_read.get("/pr/history")
def list_pr_history(
    repo_full_name: str = Query(...),
    pr_number: int = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    jobs = SupaBasePRReviewReadDB.list_jobs(repo_full_name, pr_number, limit=limit, offset=offset)

    # payload leve para lista (sem findings)
    return {
        "repo_full_name": repo_full_name,
        "pr_number": pr_number,
        "limit": limit,
        "offset": offset,
        "jobs": jobs,
    }

@router_reviews_read.get("/repos")
def list_reviewed_repos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    repos = SupaBasePRReviewReadDB.list_reviewed_repos(limit=limit, offset=offset)
    return {"limit": limit, "offset": offset, "repos": repos}

@router_reviews_read.get("/prs")
def list_reviewed_prs(
    repo_full_name: str = Query(..., description="Ex: WeslleySebastiao/chatllm-api"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    prs = SupaBasePRReviewReadDB.list_reviewed_prs_by_repo(
        repo_full_name=repo_full_name,
        limit=limit,
        offset=offset,
    )
    return {
        "repo_full_name": repo_full_name,
        "limit": limit,
        "offset": offset,
        "prs": prs,
    }
