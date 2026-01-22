import httpx

GITHUB_API = "https://api.github.com"

class GitHubClient:
    def __init__(self, token: str):
        self.token = token

    def _headers(self, accept: str = "application/vnd.github+json"):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pr-review-agent",
        }

    async def get_pr(self, repo_full_name: str, pr_number: int) -> dict:
        url = f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        url = f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(url, headers=self._headers(accept="application/vnd.github.v3.diff"))
            r.raise_for_status()
            return r.text
