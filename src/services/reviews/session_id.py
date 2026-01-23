import uuid

def pr_session_uuid(repo_full_name: str, pr_number: int, head_sha: str, agent_name: str) -> str:
    key = f"pr:{repo_full_name}:{pr_number}:{head_sha}:{agent_name}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))
