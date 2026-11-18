from pydantic import BaseModel

class AskRequest(BaseModel):
    prompt: str
    max_tokens: int

class Ask(BaseModel):
    response: str
    citations: list[dict] = []