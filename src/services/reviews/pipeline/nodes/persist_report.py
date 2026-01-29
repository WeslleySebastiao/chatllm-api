from src.services.reviews.pipeline.state import ReviewState
from src.data.supaBase.supaBase_pr_review_db import SupaBasePRReviewDB
from src.services.reviews.normalize import normalize_findings

def _extract_agents_executed(state: ReviewState) -> list[str]:
    # você pode melhorar depois. MVP: hardcoded
    return [
        "pr_review_correctness",
        "pr_review_maintainability",
        "pr_review_security",
        "pr_review_aggregator",
    ]

async def persist_report(state: ReviewState) -> dict:
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    head_sha = state["head_sha"]
    base_sha = state.get("base_sha")

    final_report = state.get("final_report") or {}
    summary_md = final_report.get("summary_md")
    findings = normalize_findings(final_report.get("findings") or [])
    tests_raw = final_report.get("tests_suggested") or []
    tests = normalize_tests(tests_raw)


    # status do job
    status = "completed"
    error = None
    if final_report.get("agent") in ("parse_error", "runtime_error"):
        status = "failed"
        error = str(final_report)

    job = SupaBasePRReviewDB.upsert_job(
        repo_full_name=repo,
        pr_number=pr_number,
        head_sha=head_sha,
        base_sha=base_sha,
        status=status,
        trigger="github_action",
        error=error,
    )

    report = SupaBasePRReviewDB.upsert_report(
        job_id=job["id"],
        summary_md=summary_md,
        result_json=final_report,
        agents_executed=_extract_agents_executed(state),
        duration_ms=None,  # depois podemos medir
    )

    SupaBasePRReviewDB.replace_findings(report_id=report["id"], findings=findings)
    SupaBasePRReviewDB.replace_test_suggestions(report_id=report["id"], tests=tests)

    # devolve ids no state (útil pro front e debug)
    return {
        "db": {
            "job_id": job["id"],
            "report_id": report["id"],
            "findings_count": len(findings),
            "tests_count": len(tests),
            "status": status,
        }
    }

def normalize_tests(tests):
    out = []
    for t in tests or []:
        if isinstance(t, str):
            s = t.strip()
            if s:
                out.append(s)
        elif isinstance(t, dict):
            # tenta chaves comuns
            s = (t.get("suggestion") or t.get("test") or t.get("title") or "").strip()
            if s:
                out.append(s)
            else:
                # fallback: serializa
                out.append(str(t))
        else:
            out.append(str(t))
    return out
