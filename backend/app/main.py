import sqlite3

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import RepositoryCreate, RepositoryOut
from backend.app.database import (
    initialize_database,
    insert_repository,
    get_all_repositories,
    get_repository_by_id,
    update_repository_github_data,
    delete_repository,
)
from backend.app.github_client import parse_github_url, fetch_repo_data
from backend.app.scoring import calculate_credibility_score


app = FastAPI(title="DevProof API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _attach_credibility_score(repository: dict) -> dict:
    if repository["stars"] is None:
        repository["credibility_score"] = None
    else:
        repository["credibility_score"] = calculate_credibility_score(
            repository["stars"], repository["forks"], repository["recent_commit_count"]
        )
    return repository


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/repositories", status_code=201)
def create_repository(repository: RepositoryCreate) -> dict[str, int | str]:
    try:
        new_id = insert_repository(repository.url)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="repository already exists")
    return {"id": new_id, "url": repository.url}


@app.get("/repositories", response_model=list[RepositoryOut])
def list_repositories() -> list[dict]:
    return [_attach_credibility_score(repository) for repository in get_all_repositories()]


@app.get("/repositories/{repository_id}", response_model=RepositoryOut)
def get_repository(repository_id: int) -> dict:
    repository = get_repository_by_id(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="repository not found")
    return _attach_credibility_score(repository)


@app.post("/repositories/{repository_id}/fetch", response_model=RepositoryOut)
def fetch_repository_data(repository_id: int) -> dict:
    repository = get_repository_by_id(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="repository not found")

    owner, repo = parse_github_url(repository["url"])

    try:
        github_data = fetch_repo_data(owner, repo)
    except requests.HTTPError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub repository not found")
        raise HTTPException(status_code=502, detail="failed to fetch data from GitHub")

    update_repository_github_data(
        repository_id,
        stars=github_data["stars"],
        forks=github_data["forks"],
        language=github_data["language"],
        description=github_data["description"],
        owner=github_data["owner"],
        recent_commit_count=github_data["recent_commit_count"],
    )

    return _attach_credibility_score(get_repository_by_id(repository_id))


@app.delete("/repositories/{repository_id}", status_code=204)
def remove_repository(repository_id: int) -> None:
    deleted = delete_repository(repository_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="repository not found")