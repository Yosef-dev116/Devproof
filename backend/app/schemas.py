from pydantic import BaseModel

class RepositoryCreate(BaseModel):
    url:str