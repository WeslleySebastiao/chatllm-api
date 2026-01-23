from starlette.concurrency import run_in_threadpool

from src.models.agent_models import AgentRunRequestV2
from src.services.reviews.agent_ids import PR_REVIEW_AGENT_IDS
from src.services.reviews.prompt_builder import build_aggregator_prompt
from src.services.reviews.pipeline.state import ReviewState
from src.services.reviews.pipeline.nodes._json_parse import safe_parse_json
from src.services.reviews.session_id import pr_session_uuid
# Ajuste o import conforme seu projeto
from src.services.agent_v2 import AgentManagerV2


async def aggregate(state: ReviewState) -> dict:
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    head_sha = state["head_sha"]
    base_session = f"pr:{repo}:{pr_number}:{head_sha}"

    user_id = state.get("user_id") or "github-actions"

    agg_prompt = build_aggregator_prompt(
        pr_title=state.get("pr_title", ""),
        pr_body=state.get("pr_body", ""),
        diff_stats=state.get("diff_stats", {}),
        specialist_outputs=state.get("specialist_outputs", []),
    )

    run_req = AgentRunRequestV2(
        agent_id=PR_REVIEW_AGENT_IDS["aggregator"],
        user_id=user_id,
        session_id=pr_session_uuid(repo, pr_number, head_sha, "pr_review_aggregator"),
        message=agg_prompt,
    )

    raw = await run_in_threadpool(AgentManagerV2.run_agent_v2, run_req)
    print("RAW_AGENT_OUTPUT =", raw)  # <-- debug
    text = raw.get("response", "")
    print("RAW_TEXT_LEN =", len(text))

    final_report = safe_parse_json(raw.get("response", ""))

    return {"final_report": final_report}
