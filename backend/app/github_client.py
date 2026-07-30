import os
from concurrent.futures import ThreadPoolExecutor

import requests

GITHUB_API_BASE = "https://api.github.com"

_session = requests.Session()

_github_token = os.environ.get("GITHUB_TOKEN")
if _github_token:
    _session.headers.update({"Authorization": f"Bearer {_github_token}"})


def parse_github_url(url: str) -> tuple[str, str]:
    owner, repo = url.rstrip("/").split("/")[-2:]
    return owner, repo


def _fetch_repo_info(owner: str, repo: str) -> dict:
    response = _session.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
    response.raise_for_status()
    return response.json()


def _fetch_commit_count(owner: str, repo: str) -> int:
    response = _session.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits")
    if response.status_code == 409:
        # GitHub returns 409 (not an empty list) when a repository has no commits yet.
        return 0
    response.raise_for_status()
    return len(response.json())


def fetch_repo_data(owner: str, repo: str) -> dict:
    with ThreadPoolExecutor(max_workers=2) as executor:
        repo_info_future = executor.submit(_fetch_repo_info, owner, repo)
        commit_count_future = executor.submit(_fetch_commit_count, owner, repo)
        repo_data = repo_info_future.result()
        recent_commit_count = commit_count_future.result()

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
    response = _session.get(
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


def fetch_repo_tree(owner: str, repo: str, default_branch: str) -> list[dict]:
    response = _session.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}",
        params={"recursive": "1"},
    )
    if response.status_code in (404, 409):
        # Empty repository (no commits yet) has no tree to fetch.
        return []
    response.raise_for_status()
    return [
        {"path": entry["path"], "size": entry.get("size", 0)}
        for entry in response.json()["tree"]
        if entry["type"] == "blob"
    ]


def fetch_readme_text(owner: str, repo: str) -> str | None:
    response = _session.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme",
        headers={"Accept": "application/vnd.github.raw+json"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.text


def fetch_tree_and_readme(owner: str, repo: str, default_branch: str) -> tuple[list[dict], str | None]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        tree_future = executor.submit(fetch_repo_tree, owner, repo, default_branch)
        readme_future = executor.submit(fetch_readme_text, owner, repo)
        return tree_future.result(), readme_future.result()


def fetch_file_content(owner: str, repo: str, path: str) -> str | None:
    response = _session.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
        headers={"Accept": "application/vnd.github.raw+json"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.text


def fetch_sample_files(owner: str, repo: str, paths: list[str]) -> dict[str, str]:
    if not paths:
        return {}
    with ThreadPoolExecutor(max_workers=len(paths)) as executor:
        futures = {path: executor.submit(fetch_file_content, owner, repo, path) for path in paths}
        results = {path: future.result() for path, future in futures.items()}
    return {path: content for path, content in results.items() if content is not None}


def fetch_user_profile(username: str) -> dict:
    response = _session.get(f"{GITHUB_API_BASE}/users/{username}")
    response.raise_for_status()
    data = response.json()
    return {
        "login": data["login"],
        "name": data.get("name"),
        "bio": data.get("bio"),
        "public_repos": data.get("public_repos"),
        "followers": data.get("followers"),
        "account_created_at": data.get("created_at"),
    }


def fetch_profile_and_repos(username: str) -> tuple[dict, list[dict]]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        profile_future = executor.submit(fetch_user_profile, username)
        repos_future = executor.submit(list_public_repos, username)
        return profile_future.result(), repos_future.result()


def list_org_repos(org: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        response = _session.get(
            f"{GITHUB_API_BASE}/orgs/{org}/repos",
            params={"per_page": 100, "page": page, "type": "public"},
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [
        {"name": repo["name"], "full_name": repo["full_name"], "fork": repo["fork"]}
        for repo in repos
    ]


def fetch_repo_contributors(owner: str, repo: str) -> list[dict]:
    contributors: list[dict] = []
    page = 1
    while True:
        response = _session.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors",
            params={"per_page": 100, "page": page},
        )
        if response.status_code in (204, 403):
            # 204: empty repository, no contributors to compute.
            # 403: GitHub refuses to compute contributor stats for some repos
            # (e.g. very large ones) - skip rather than fail the whole org.
            break
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        contributors.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [
        {"login": c["login"], "avatar_url": c.get("avatar_url"), "contributions": c["contributions"]}
        for c in contributors
        if c.get("type") != "Bot"
    ]


def fetch_contributors_for_repos(owner: str, repo_names: list[str]) -> dict[str, list[dict]]:
    if not repo_names:
        return {}
    with ThreadPoolExecutor(max_workers=min(len(repo_names), 10)) as executor:
        futures = {name: executor.submit(fetch_repo_contributors, owner, name) for name in repo_names}
        return {name: future.result() for name, future in futures.items()}
