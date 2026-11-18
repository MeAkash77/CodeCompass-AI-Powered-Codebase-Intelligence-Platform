from sqlalchemy import Column, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from pgvector.sqlalchemy import Vector

from app.db.db import Base

class RagDocChunk(Base):
    __tablename__ = "rag_doc_chunk"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("rag_doc_parent.id", ondelete="CASCADE"))
    parent_url = Column(Text)
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding = Column(Vector(768)) 
    tsv = Column(TSVECTOR) 
    meta_data = Column(MutableDict.as_mutable(JSONB))

    __table_args__ = (
        UniqueConstraint("parent_id", "chunk_index", name="uq_rag_doc_chunk_parent_chunkindex"),
        Index("idx_chunk_tsv", "tsv", postgresql_using="gin"),
        Index("idx_chunk_embedding", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 100}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

    parent = relationship("RagDocParent", back_populates="chunks")