from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.exceptions import DocumentAlreadyExistsError, DocumentNotFoundError
from .engine import MemoryBankEngine
from .models import MemoryDocument
from .repository import MemoryRepository
from .schemas import DocumentContent, DocumentCreate, DocumentListResponse, DocumentResponse, DocumentUpdate, SyncResponse


class MemoryService:
    def __init__(self, db: Session, engine: MemoryBankEngine | None = None) -> None:
        self.db = db
        self.engine = engine or MemoryBankEngine()
        self.repo = MemoryRepository(db)

    # ------------------------------------------------------------------ CRUD

    def create(self, payload: DocumentCreate) -> DocumentResponse:
        if self.repo.get_by_slug(payload.slug) is not None:
            raise DocumentAlreadyExistsError(payload.slug)
        if self.engine.exists(payload.slug):
            raise DocumentAlreadyExistsError(payload.slug)
        doc = self.engine.write(payload.slug, payload.title, payload.content, payload.category, payload.tags)
        db_doc = self.repo.create(doc)
        self._fts_upsert(db_doc)
        return DocumentResponse.model_validate(db_doc)

    def get(self, slug: str) -> DocumentResponse:
        db_doc = self.repo.get_by_slug(slug)
        if db_doc is None:
            raise DocumentNotFoundError(slug)
        return DocumentResponse.model_validate(db_doc)

    def update(self, slug: str, payload: DocumentUpdate) -> DocumentResponse:
        db_doc = self.repo.get_by_slug(slug)
        if db_doc is None:
            raise DocumentNotFoundError(slug)
        existing = self.engine.read(slug)
        doc = self.engine.write(
            slug=slug,
            title=payload.title if payload.title is not None else db_doc.title,
            body=payload.content if payload.content is not None else existing.content,
            category=payload.category if payload.category is not None else db_doc.category,
            tags=payload.tags if payload.tags is not None else list(db_doc.tags),
        )
        updated = self.repo.update(db_doc, doc)
        self._fts_upsert(updated)
        return DocumentResponse.model_validate(updated)

    def delete(self, slug: str) -> None:
        db_doc = self.repo.get_by_slug(slug)
        if db_doc is None:
            raise DocumentNotFoundError(slug)
        self.engine.delete(slug)
        self._fts_delete(slug)
        self.repo.delete(db_doc)

    def list_all(
        self,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DocumentListResponse:
        docs = self.repo.list_all(category=category, limit=limit, offset=offset)
        total = self.repo.count()
        return DocumentListResponse(total=total, items=[DocumentResponse.model_validate(d) for d in docs])

    # ------------------------------------------------------------------ Search

    def search_fts(self, query: str, limit: int = 20) -> DocumentListResponse:
        """Keyword search via SQLite FTS5. Returns ranked ORM objects (JSON cols deserialised)."""
        # FTS gives us ranked slugs; we then load full ORM objects so JSON fields deserialise correctly.
        slug_rows = self.db.execute(
            text("SELECT slug FROM memory_fts WHERE memory_fts MATCH :query ORDER BY rank LIMIT :limit"),
            {"query": query, "limit": limit},
        ).fetchall()
        slugs = [row[0] for row in slug_rows]
        docs = [self.repo.get_by_slug(s) for s in slugs]
        items = [DocumentResponse.model_validate(d) for d in docs if d is not None]
        return DocumentListResponse(total=len(items), items=items)

    # ------------------------------------------------------------------ Sync

    def sync_from_disk(self) -> SyncResponse:
        """Index all Markdown files from disk into SQLite. Skips unchanged files."""
        all_docs = self.engine.read_all()
        synced = 0
        for doc in all_docs:
            existing = self.repo.get_by_slug(doc.slug)
            if existing is None:
                db_doc = self.repo.create(doc)
                self._fts_upsert(db_doc)
                synced += 1
            elif existing.checksum != doc.checksum:
                db_doc = self.repo.update(existing, doc)
                self._fts_upsert(db_doc)
                synced += 1
        return SyncResponse(synced=synced, message=f"Synced {synced} document(s) from disk.")

    # ------------------------------------------------------------------ FTS helpers

    def _fts_upsert(self, doc: MemoryDocument) -> None:
        self.db.execute(text("DELETE FROM memory_fts WHERE slug = :slug"), {"slug": doc.slug})
        self.db.execute(
            text("INSERT INTO memory_fts (slug, title, content) VALUES (:slug, :title, :content)"),
            {"slug": doc.slug, "title": doc.title, "content": doc.content},
        )
        self.db.commit()

    def _fts_delete(self, slug: str) -> None:
        self.db.execute(text("DELETE FROM memory_fts WHERE slug = :slug"), {"slug": slug})
        self.db.commit()
