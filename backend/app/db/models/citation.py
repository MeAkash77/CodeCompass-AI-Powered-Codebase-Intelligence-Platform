from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.db import Base

class Citation(Base):
    __tablename__ = "citation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversation_history.id"), nullable=False)
    conversation_history = relationship("ConversationHistory", back_populates="citations")