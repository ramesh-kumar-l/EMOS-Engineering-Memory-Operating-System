from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import MemoryDocument
from .schemas import DocumentContent


class MemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_slug(self, slug: str) -> MemoryDocument | None:
        return self.db.scalar(select(MemoryDocument).where(MemoryDocument.slug == slug))

    def get_by_id(self, doc_id: str) -> MemoryDocument | None:
        return self.db.get(MemoryDocument, doc_id)

    def list_all(
        self,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryDocument]:
        q = select(MemoryDocument)
        if category:
            q = q.where(MemoryDocument.category == category)
        q = q.order_by(MemoryDocument.updated_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(q).all())

    def count(self) -> int:
        return self.db.scalar(select(func.count(MemoryDocument.id))) or 0

    def create(self, doc: DocumentContent) -> MemoryDocument:
        now = datetime.now(timezone.utc)
        db_doc = MemoryDocument(
            id=str(uuid4()),
            slug=doc.slug,
            title=doc.title,
            content=doc.content,
            category=doc.category,
            tags=doc.tags,
            file_path=doc.file_path,
            checksum=doc.checksum,
            word_count=doc.word_count,
            is_indexed=False,
            created_at=now,
            updated_at=now,
        )
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)
        return db_doc

    def update(self, db_doc: MemoryDocument, doc: DocumentContent) -> MemoryDocument:
        db_doc.title = doc.title
        db_doc.content = doc.content
        db_doc.category = doc.category
        db_doc.tags = doc.tags
        db_doc.file_path = doc.file_path
        db_doc.checksum = doc.checksum
        db_doc.word_count = doc.word_count
        db_doc.updated_at = datetime.now(timezone.utc)
        db_doc.is_indexed = False
        self.db.commit()
        self.db.refresh(db_doc)
        return db_doc

    def delete(self, db_doc: MemoryDocument) -> None:
        self.db.delete(db_doc)
        self.db.commit()
