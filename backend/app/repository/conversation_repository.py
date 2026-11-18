from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from app.db.models.conversation_history import ConversationHistory
from app.db.models.citation import Citation

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_conversation(self, session_id: str, role: str, content: str, citations: list[dict] = []):
        """ Save conversation """
        new_conversation = ConversationHistory(session_id=session_id, role=role, content=content)
        self.db.add(new_conversation)
        self.db.flush()

        if citations:
            for citation in citations:
                new_citation = Citation(
                    title=citation["title"],
                    url=citation["url"],
                    conversation_id=new_conversation.id
                )
                self.db.add(new_citation)
        self.db.commit()
        self.db.refresh(new_conversation)

        return new_conversation
        

    def get_all_conversations(self, session_id: str):
        """ Fetch all conversations for a session """
        conversations = self.db.execute(
            select(ConversationHistory)
            .options(joinedload(ConversationHistory.citations))
            .where(ConversationHistory.session_id == session_id)
            .order_by(ConversationHistory.created_at)
        ).unique().scalars().all()
        return conversations

    def get_top_n_conversations(self, session_id: str, n: int):
        """ Fetch top-N latest conversations for a session """
        conversations = self.db.execute(
            select(ConversationHistory)
            .where(ConversationHistory.session_id == session_id)
            .order_by(desc(ConversationHistory.created_at))
            .limit(n)
        ).scalars().all()
        return conversations