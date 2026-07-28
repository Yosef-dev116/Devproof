import sqlite3

from fastapi import FastAPI, HTTPException

from backend.app.schemas import RepositoryCreate
from backend.app.database import initialize_database, insert_repository


app = FastAPI(title="DevProof API")


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