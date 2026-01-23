from src.services.reviews.github_client import GitHubClient
from src.services.reviews.pipeline.state import ReviewState

async def ingest_pr(state: ReviewState) -> dict:
    gh = GitHubClient(token=state["github_token"])
    pr = await gh.get_pr(state["repo_full_name"], state["pr_number"])
    diff_text = await gh.get_pr_diff(state["repo_full_name"], state["pr_number"])

    # MVP: corte simples para evitar prompt gigante
    MAX_CHARS = 120_000
    truncated = False
    if len(diff_text) > MAX_CHARS:
        diff_text = diff_text[:MAX_CHARS] + "\n\n[TRUNCATED_DIFF]\n"
        truncated = True

    patch = {
        "pr_title": pr.get("title", "") or "",
        "pr_body": pr.get("body", "") or "",
        "diff_text": diff_text,
        "diff_stats": {
            "head_sha": state["head_sha"],
            "base_sha": state["base_sha"],
            "diff_chars": len(diff_text),
            "truncated": truncated,
            "files_changed": pr.get("changed_files"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
        }
    }
    return patch
