import requests

GITHUB_API_BASE = "https://api.github.com"


def parse_github_url(url: str) -> tuple[str, str]:
    owner, repo = url.rstrip("/").split("/")[-2:]
    return owner, repo


def fetch_repo_data(owner: str, repo: str) -> dict:
    repo_response = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
    repo_response.raise_for_status()
    repo_data = repo_response.json()

    commits_response = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits")
    if commits_response.status_code == 409:
        # GitHub returns 409 (not an empty list) when a repository has no commits yet.
        recent_commit_count = 0
    else:
        commits_response.raise_for_status()
        recent_commit_count = len(commits_response.json())

    return {
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "language": repo_data["language"],
        "description": repo_data["description"],
        "owner": repo_data["owner"]["login"],
        "recent_commit_count": recent_commit_count,
        "default_branch": repo_data["default_branch"],
    }


def list_public_repos(username: str) -> list[dict]:
    response = requests.get(
        f"{GITHUB_API_BASE}/users/{username}/repos",
        params={"per_page": 100, "sort": "updated"},
    )
    response.raise_for_status()
    return [
        {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "html_url": repo["html_url"],
            "description": repo["description"],
            "stargazers_count": repo["stargazers_count"],
            "language": repo["language"],
        }
        for repo in response.json()
    ]


def fetch_repo_tree(owner: str, repo: str, default_branch: str) -> list[str]:
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}",
        params={"recursive": "1"},
    )
    if response.status_code in (404, 409):
        # Empty repository (no commits yet) has no tree to fetch.
        return []
    response.raise_for_status()
    return [entry["path"] for entry in response.json()["tree"]]


def fetch_readme_text(owner: str, repo: str) -> str | None:
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme",
        headers={"Accept": "application/vnd.github.raw+json"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.text
