from typing import TypedDict, Optional, Any

class ReviewState(TypedDict, total=False):
    # input inicial do endpoint
    github_token: str
    repo_full_name: str
    pr_number: int
    head_sha: str
    base_sha: str
    user_id: str

    # preenchido no ingest_pr
    pr_title: str
    pr_body: str
    diff_text: str
    diff_stats: dict

    # preenchido no run_specialists
    specialist_outputs: list[dict]

    # preenchido no aggregate
    final_report: dict

    # diagnóstico/erros
    errors: list[dict]
