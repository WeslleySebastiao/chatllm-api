def build_specialist_prompt(agent_name: str, pr_title: str, pr_body: str, diff_text: str) -> str:
    body = pr_body or ""
    return f"""
[AGENT]
{agent_name}

[PR]
title: {pr_title}
description: {body}

[DIFF]
{diff_text}
""".strip()

def build_aggregator_prompt(pr_title: str, pr_body: str, diff_stats: dict, specialist_outputs: list[dict]) -> str:
    body = pr_body or ""
    return f"""
[PR]
title: {pr_title}
description: {body}

[DIFF_STATS]
{diff_stats}

[SPECIALIST_OUTPUTS_JSON]
{specialist_outputs}
""".strip()
