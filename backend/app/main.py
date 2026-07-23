from fastapi import FastAPI
from backend.app.schemas import RepositoryCreate
from backend.app.database import initialize_database,insert_repository


app = FastAPI(title="DevProof API")


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/repositories", status_code =201)
def create_repository(repository: RepositoryCreate) -> dict[str, int | str]:
    new_id = insert_repository(repository.url)
    return {"id": new_id, "url":repository.url}