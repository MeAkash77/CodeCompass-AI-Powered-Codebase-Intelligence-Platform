from sqlalchemy import Column, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict

from app.db.db import Base

class RagDocParent(Base):
    __tablename__ = "rag_doc_parent"

    id = Column(Integer, primary_key=True)
    url = Column(Text)
    title = Column(Text)
    section = Column(Text)
    subsection = Column(Text)
    content = Column(Text)
    meta_data = Column(MutableDict.as_mutable(JSONB))

    __table_args__ = (
        UniqueConstraint("url", "subsection", name="uq_rag_doc_parent_url_subsection"),
    )

    chunks = relationship(
        "RagDocChunk",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True
    )