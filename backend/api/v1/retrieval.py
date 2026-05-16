from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.database import get_db
from ...core.exceptions import IndexNotReadyError, to_http
from ...retrieval.embedder import Embedder
from ...retrieval.index import FAISSIndex
from ...retrieval.schemas import IndexResponse, IndexStatus, RetrievalResponse
from ...retrieval.service import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

_embedder: Embedder | None = None
_faiss_index: FAISSIndex | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def get_faiss_index() -> FAISSIndex:
    global _faiss_index
    if _faiss_index is None:
        _faiss_index = FAISSIndex(get_settings().faiss_index_dir)
    return _faiss_index


def _service(
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    index: FAISSIndex = Depends(get_faiss_index),
) -> RetrievalService:
    return RetrievalService(db, embedder, index)


@router.get("/search", response_model=RetrievalResponse, summary="Hybrid / semantic / keyword search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    alpha: float = Query(
        0.5, ge=0.0, le=1.0,
        description="Semantic weight in hybrid mode (0.0 = keyword only, 1.0 = semantic only)",
    ),
    mode: str = Query("hybrid", description="Search mode: hybrid | semantic | keyword"),
    svc: RetrievalService = Depends(_service),
) -> RetrievalResponse:
    try:
        return svc.search(q, limit=limit, alpha=alpha, mode=mode)
    except IndexNotReadyError as e:
        raise to_http(e)


@router.post("/index", response_model=IndexResponse, summary="Build or rebuild the FAISS vector index")
def build_index(svc: RetrievalService = Depends(_service)) -> IndexResponse:
    return svc.build_index()


@router.get("/status", response_model=IndexStatus, summary="Get FAISS index statistics")
def index_status(svc: RetrievalService = Depends(_service)) -> IndexStatus:
    return svc.index_status()
