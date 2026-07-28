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
    }
