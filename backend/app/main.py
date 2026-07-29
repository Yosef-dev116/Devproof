import json
import secrets
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Point load_dotenv() at the exact file rather than relying on its default
# auto-discovery (stack-based, walking up from the caller's file). That
# discovery silently fails when uvicorn's --reload spawns its worker via
# Windows' multiprocessing "spawn" method, which doesn't preserve the same
# stack context - an explicit path works regardless of how the process started.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend.app.schemas import RepositoryCreate, RepositoryOut
from backend.app.database import (
    initialize_database,
    insert_repository,
    get_all_repositories,
    get_repository_by_id,
    update_repository_github_data,
    update_repository_analysis,
    delete_repository,
    get_or_create_user,
    create_session,
    get_user_by_session,
    delete_session,
)
from backend.app.auth import (
    get_github_login_url,
    exchange_code_for_token,
    fetch_github_profile,
)
from backend.app.github_client import (
    parse_github_url,
    fetch_repo_data,
    list_public_repos,
    fetch_tree_and_readme,
)
from backend.app.analysis import detect_signals
from backend.app.ai_report import generate_report, AIReportError
from backend.app.scoring import calculate_credibility_score


app = FastAPI(title="DevProof API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(session_id: str | None = Cookie(default=None)) -> dict:
    user = get_user_by_session(session_id) if session_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


def _attach_credibility_score(repository: dict) -> dict:
    if repository["stars"] is None:
        repository["credibility_score"] = None
    else:
        repository["credibility_score"] = calculate_credibility_score(
            repository["stars"], repository["forks"], repository["recent_commit_count"]
        )
    return repository


def _attach_parsed_report(repository: dict) -> dict:
    repository["analysis_report"] = (
        json.loads(repository["analysis_report"]) if repository["analysis_report"] else None
    )
    return repository


def _decorate(repository: dict) -> dict:
    return _attach_parsed_report(_attach_credibility_score(repository))


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/github/login")
def github_login() -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    redirect = RedirectResponse(get_github_login_url(state))
    redirect.set_cookie("oauth_state", state, httponly=True, samesite="lax", max_age=600)
    return redirect


@app.get("/auth/github/callback")
def github_callback(code: str, state: str, oauth_state: str | None = Cookie(default=None)) -> RedirectResponse:
    if not oauth_state or state != oauth_state:
        raise HTTPException(status_code=400, detail="invalid oauth state")

    access_token = exchange_code_for_token(code)
    profile = fetch_github_profile(access_token)
    user = get_or_create_user(profile["id"], profile["login"], profile["avatar_url"], access_token)
    session_id = create_session(user["id"])

    redirect = RedirectResponse("http://localhost:5180/")
    redirect.delete_cookie("oauth_state")
    redirect.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return redirect


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "github_username": current_user["github_username"],
        "avatar_url": current_user["avatar_url"],
    }


@app.post("/auth/logout", status_code=204)
def logout(response: Response, session_id: str | None = Cookie(default=None)) -> None:
    if session_id:
        delete_session(session_id)
    response.delete_cookie("session_id")


@app.get("/github/{username}/repos")
def list_github_repos(username: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    try:
        return list_public_repos(username)
    except requests.HTTPError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        raise HTTPException(
            status_code=502,
            detail=f"failed to fetch repositories from GitHub (GitHub returned {error.response.status_code})",
        )


@app.post("/repositories", status_code=201)
def create_repository(repository: RepositoryCreate, current_user: dict = Depends(get_current_user)) -> dict[str, int | str]:
    try:
        new_id = insert_repository(repository.url, current_user["id"])
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="repository already exists")
    return {"id": new_id, "url": repository.url}


@app.get("/repositories", response_model=list[RepositoryOut])
def list_repositories(current_user: dict = Depends(get_current_user)) -> list[dict]:
    return [_decorate(repository) for repository in get_all_repositories(current_user["id"])]


@app.get("/repositories/{repository_id}", response_model=RepositoryOut)
def get_repository(repository_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    repository = get_repository_by_id(repository_id, current_user["id"])
    if repository is None:
        raise HTTPException(status_code=404, detail="repository not found")
    return _decorate(repository)


def _fetch_and_store_github_data(repository_id: int, user_id: int, url: str) -> dict:
    owner, repo = parse_github_url(url)
    try:
        github_data = fetch_repo_data(owner, repo)
    except requests.HTTPError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub repository not found")
        raise HTTPException(
            status_code=502,
            detail=f"failed to fetch data from GitHub (GitHub returned {error.response.status_code})",
        )

    update_repository_github_data(
        repository_id,
        user_id,
        stars=github_data["stars"],
        forks=github_data["forks"],
        language=github_data["language"],
        description=github_data["description"],
        owner=github_data["owner"],
        recent_commit_count=github_data["recent_commit_count"],
    )
    return github_data


@app.post("/repositories/{repository_id}/fetch", response_model=RepositoryOut)
def fetch_repository_data(repository_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    repository = get_repository_by_id(repository_id, current_user["id"])
    if repository is None:
        raise HTTPException(status_code=404, detail="repository not found")

    _fetch_and_store_github_data(repository_id, current_user["id"], repository["url"])

    return _decorate(get_repository_by_id(repository_id, current_user["id"]))


@app.post("/repositories/{repository_id}/analyze", response_model=RepositoryOut)
def analyze_repository(repository_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    repository = get_repository_by_id(repository_id, current_user["id"])
    if repository is None:
        raise HTTPException(status_code=404, detail="repository not found")

    owner, repo = parse_github_url(repository["url"])
    github_data = _fetch_and_store_github_data(repository_id, current_user["id"], repository["url"])
    repository = get_repository_by_id(repository_id, current_user["id"])

    try:
        file_paths, readme_text = fetch_tree_and_readme(owner, repo, github_data["default_branch"])
    except requests.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"failed to fetch repository contents from GitHub (GitHub returned {error.response.status_code})",
        )

    signals = detect_signals(file_paths)

    evidence = {
        "stars": repository["stars"],
        "forks": repository["forks"],
        "language": repository["language"],
        "description": repository["description"],
        "recent_commit_count": repository["recent_commit_count"],
        **signals,
        "readme_excerpt": (readme_text or "")[:1500],
    }

    try:
        report = generate_report(evidence)
    except AIReportError as error:
        raise HTTPException(status_code=502, detail=f"failed to generate AI report: {error}")

    update_repository_analysis(repository_id, current_user["id"], report)

    return _decorate(get_repository_by_id(repository_id, current_user["id"]))


@app.delete("/repositories/{repository_id}", status_code=204)
def remove_repository(repository_id: int, current_user: dict = Depends(get_current_user)) -> None:
    deleted = delete_repository(repository_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="repository not found")
