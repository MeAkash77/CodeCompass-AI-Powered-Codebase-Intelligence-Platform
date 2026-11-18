from pydantic import BaseModel
from datetime import datetime
from app.db.models.conversation_history import ConversationHistory

class ConversationResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
    citations: list[dict]

def map_to_dto(conv: ConversationHistory):
    return ConversationResponse(
        role=conv.role,             # type: ignore
        content=conv.content,       # type: ignore
        created_at=conv.created_at, # type: ignore
        citations=[{
            "title": c.title,
            "url": c.url,
        } for c in conv.citations]
    )
