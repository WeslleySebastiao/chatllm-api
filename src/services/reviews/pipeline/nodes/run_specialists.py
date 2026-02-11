from starlette.concurrency import run_in_threadpool

from src.models.agent_models import AgentRunRequestV2
from src.services.reviews.agent_ids import PR_REVIEW_AGENT_IDS
from src.services.reviews.prompt_builder import build_specialist_prompt
from src.services.reviews.pipeline.state import ReviewState
from src.services.reviews.pipeline.nodes._json_parse import safe_parse_json
from src.services.reviews.session_id import pr_session_uuid
# Ajuste o import conforme seu projeto
from src.services.agent_v2 import AgentManagerV2


async def run_specialists(state: ReviewState) -> dict:
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    head_sha = state["head_sha"]

    base_session = f"pr:{repo}:{pr_number}:{head_sha}"
    user_id = state.get("user_id") or "github-actions"

    specialist_runs = [
        ("pr_review_correctness", PR_REVIEW_AGENT_IDS["correctness"]),
        ("pr_review_maintainability", PR_REVIEW_AGENT_IDS["maintainability"]),
        ("pr_review_security", PR_REVIEW_AGENT_IDS["security"]),
    ]

    outputs: list[dict] = []

    for agent_name, agent_id in specialist_runs:
        user_prompt = build_specialist_prompt(
            agent_name=agent_name,
            pr_title=state.get("pr_title", ""),
            pr_body=state.get("pr_body", ""),
            diff_text=state.get("diff_text", ""),
        )

        run_req = AgentRunRequestV2(
            agent_id=agent_id,
            user_id=user_id,
            session_id=pr_session_uuid(repo, pr_number, head_sha, agent_name),
            message=user_prompt,
        )

        # roda o agente sem bloquear o event loop
        raw = await AgentManagerV2.run_agent_v2(run_req)

        print("RAW_AGENT_OUTPUT =", raw)  # <-- debug
        text = raw.get("response", "")
        print("RAW_TEXT_LEN =", len(text))
        
        parsed = safe_parse_json(raw.get("response", ""))
        outputs.append(parsed)

    return {"specialist_outputs": outputs}
