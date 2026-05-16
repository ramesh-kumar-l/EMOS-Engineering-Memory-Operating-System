from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.exceptions import DocumentAlreadyExistsError, DocumentNotFoundError, to_http
from ...memory.engine import MemoryBankEngine
from ...memory.schemas import DocumentCreate, DocumentListResponse, DocumentResponse, DocumentUpdate, SyncResponse
from ...memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


def get_mem_engine() -> MemoryBankEngine:
    return MemoryBankEngine()


def _service(
    db: Session = Depends(get_db),
    engine: MemoryBankEngine = Depends(get_mem_engine),
) -> MemoryService:
    return MemoryService(db, engine)


@router.get("", response_model=DocumentListResponse, summary="List all documents")
def list_documents(
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    svc: MemoryService = Depends(_service),
) -> DocumentListResponse:
    return svc.list_all(category=category, limit=limit, offset=offset)


@router.post("", response_model=DocumentResponse, status_code=201, summary="Create a document")
def create_document(
    payload: DocumentCreate,
    svc: MemoryService = Depends(_service),
) -> DocumentResponse:
    try:
        return svc.create(payload)
    except DocumentAlreadyExistsError as e:
        raise to_http(e)


@router.get("/search", response_model=DocumentListResponse, summary="Full-text search")
def search_documents(
    q: str = Query(..., min_length=1, description="FTS5 query string"),
    limit: int = Query(20, ge=1, le=100),
    svc: MemoryService = Depends(_service),
) -> DocumentListResponse:
    return svc.search_fts(q, limit=limit)


@router.post("/sync", response_model=SyncResponse, summary="Sync Markdown files from disk into SQLite")
def sync_from_disk(svc: MemoryService = Depends(_service)) -> SyncResponse:
    return svc.sync_from_disk()


@router.get("/{slug}", response_model=DocumentResponse, summary="Get a document by slug")
def get_document(slug: str, svc: MemoryService = Depends(_service)) -> DocumentResponse:
    try:
        return svc.get(slug)
    except DocumentNotFoundError as e:
        raise to_http(e)


@router.put("/{slug}", response_model=DocumentResponse, summary="Update a document")
def update_document(
    slug: str,
    payload: DocumentUpdate,
    svc: MemoryService = Depends(_service),
) -> DocumentResponse:
    try:
        return svc.update(slug, payload)
    except DocumentNotFoundError as e:
        raise to_http(e)


@router.delete("/{slug}", status_code=204, summary="Delete a document")
def delete_document(slug: str, svc: MemoryService = Depends(_service)) -> None:
    try:
        svc.delete(slug)
    except DocumentNotFoundError as e:
        raise to_http(e)
