from pydantic import BaseModel

class RepositoryCreate(BaseModel):
    url: str

class RepositoryOut(BaseModel):
    id: int
    url: str
    created_at: str