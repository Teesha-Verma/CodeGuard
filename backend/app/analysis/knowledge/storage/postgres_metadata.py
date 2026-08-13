import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Index
from sqlalchemy.orm import Session

from app.db.database import Base, SessionLocal

logger = logging.getLogger(__name__)

# SQLAlchemy ORM Models
class KnowledgeDocumentRecord(Base):
    __tablename__ = "knowledge_documents"
    
    document_id = Column(String(64), primary_key=True)
    title = Column(String(512), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    source = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    version = Column(String(32), default="1.0.0")
    language = Column(String(16), default="en")
    chunk_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class KnowledgeChunkRecord(Base):
    __tablename__ = "knowledge_chunks"
    
    chunk_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    tags = Column(JSON, default=list)
    content_preview = Column(Text)  # First 200 chars for debugging
    token_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Add composite index on (document_id, chunk_index)
Index("ix_knowledge_chunks_doc_idx", KnowledgeChunkRecord.document_id, KnowledgeChunkRecord.chunk_index)


class PostgresMetadataStore:
    """PostgreSQL-backed metadata storage for knowledge documents and chunks."""
    
    def __init__(self, session_factory=None):
        self._session_factory = session_factory or SessionLocal
    
    def save_document(self, doc_id: str, title: str, category: str, source: str, tags: list[str], version: str, language: str, chunk_count: int, metadata: dict) -> None:
        with self._session_factory() as session:
            try:
                record = session.query(KnowledgeDocumentRecord).filter_by(document_id=doc_id).first()
                if not record:
                    record = KnowledgeDocumentRecord(document_id=doc_id)
                    session.add(record)
                
                record.title = title
                record.category = category
                record.source = source
                record.tags = tags
                record.version = version
                record.language = language
                record.chunk_count = chunk_count
                record.metadata_ = metadata
                
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving document {doc_id}: {e}")
                raise
    
    def get_document(self, doc_id: str) -> dict | None:
        with self._session_factory() as session:
            record = session.query(KnowledgeDocumentRecord).filter_by(document_id=doc_id).first()
            if not record:
                return None
            return {
                "document_id": record.document_id,
                "title": record.title,
                "category": record.category,
                "source": record.source,
                "tags": record.tags,
                "version": record.version,
                "language": record.language,
                "chunk_count": record.chunk_count,
                "metadata": record.metadata_,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            }
    
    def list_documents(self, category: str | None = None, tag: str | None = None) -> list[dict]:
        with self._session_factory() as session:
            query = session.query(KnowledgeDocumentRecord)
            if category:
                query = query.filter_by(category=category)
            
            records = query.all()
            results = []
            for record in records:
                if tag and (not record.tags or tag not in record.tags):
                    continue
                results.append({
                    "document_id": record.document_id,
                    "title": record.title,
                    "category": record.category,
                    "source": record.source,
                    "tags": record.tags,
                    "version": record.version,
                    "language": record.language,
                    "chunk_count": record.chunk_count,
                    "metadata": record.metadata_,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at
                })
            return results
    
    def delete_document(self, doc_id: str) -> bool:
        with self._session_factory() as session:
            try:
                record = session.query(KnowledgeDocumentRecord).filter_by(document_id=doc_id).first()
                if record:
                    session.delete(record)
                    session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting document {doc_id}: {e}")
                raise
    
    def save_chunk_metadata(self, chunk_id: str, document_id: str, chunk_index: int, category: str, tags: list[str], content_preview: str, token_count: int, metadata: dict) -> None:
        with self._session_factory() as session:
            try:
                record = session.query(KnowledgeChunkRecord).filter_by(chunk_id=chunk_id).first()
                if not record:
                    record = KnowledgeChunkRecord(chunk_id=chunk_id)
                    session.add(record)
                
                record.document_id = document_id
                record.chunk_index = chunk_index
                record.category = category
                record.tags = tags
                record.content_preview = content_preview
                record.token_count = token_count
                record.metadata_ = metadata
                
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving chunk {chunk_id}: {e}")
                raise
    
    def get_chunk_metadata(self, chunk_id: str) -> dict | None:
        with self._session_factory() as session:
            record = session.query(KnowledgeChunkRecord).filter_by(chunk_id=chunk_id).first()
            if not record:
                return None
            return {
                "chunk_id": record.chunk_id,
                "document_id": record.document_id,
                "chunk_index": record.chunk_index,
                "category": record.category,
                "tags": record.tags,
                "content_preview": record.content_preview,
                "token_count": record.token_count,
                "metadata": record.metadata_,
                "created_at": record.created_at
            }
    
    def get_chunks_by_document(self, document_id: str) -> list[dict]:
        with self._session_factory() as session:
            records = session.query(KnowledgeChunkRecord).filter_by(document_id=document_id).order_by(KnowledgeChunkRecord.chunk_index).all()
            return [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "chunk_index": r.chunk_index,
                    "category": r.category,
                    "tags": r.tags,
                    "content_preview": r.content_preview,
                    "token_count": r.token_count,
                    "metadata": r.metadata_,
                    "created_at": r.created_at
                }
                for r in records
            ]
    
    def delete_chunks_by_document(self, document_id: str) -> int:
        with self._session_factory() as session:
            try:
                deleted_count = session.query(KnowledgeChunkRecord).filter_by(document_id=document_id).delete()
                session.commit()
                return deleted_count
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting chunks for document {document_id}: {e}")
                raise
    
    def ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        from app.db.database import engine
        try:
            Base.metadata.create_all(bind=engine, tables=[KnowledgeDocumentRecord.__table__, KnowledgeChunkRecord.__table__])
            logger.info("Knowledge tables created successfully or already exist.")
        except Exception as e:
            logger.error(f"Error creating knowledge tables: {e}")
            raise
