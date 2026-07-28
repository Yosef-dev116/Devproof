from pydantic import BaseModel

class RepositoryCreate(BaseModel):
    url: str

class RepositoryOut(BaseModel):
    id: int
    url: str
    created_at: str
    stars: int | None = None
    forks: int | None = None
    language: str | None = None
    description: str | None = None
    owner: str | None = None
    recent_commit_count: int | None = None
    last_fetched_at: str | None = None
    credibility_score: int | None = None
    analysis_report: dict | None = None
    analyzed_at: str | None = None