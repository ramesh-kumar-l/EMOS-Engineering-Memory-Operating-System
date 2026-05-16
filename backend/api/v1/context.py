from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...context.client import AIClient, ClaudeClient
from ...context.schemas import ContextRequest, ContextResponse, ContextStatus
from ...context.service import ContextService
from ...core.config import get_settings
from ...core.database import get_db
from ...core.exceptions import ClaudeNotConfiguredError, IndexNotReadyError
from ...retrieval.embedder import Embedder
from ...retrieval.index import FAISSIndex
from .retrieval import get_embedder, get_faiss_index

router = APIRouter(prefix="/context", tags=["context"])

_claude_client: AIClient | None = None


def get_claude_client() -> AIClient | None:
    global _claude_client
    if _claude_client is None:
        settings = get_settings()
        if settings.anthropic_api_key:
            _claude_client = ClaudeClient(settings.anthropic_api_key)
    return _claude_client


def _service(
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    index: FAISSIndex = Depends(get_faiss_index),
    claude: AIClient | None = Depends(get_claude_client),
) -> ContextService:
    return ContextService(db, embedder, index, claude)


@router.post("/assemble", response_model=ContextResponse, summary="Assemble a token-budgeted context package")
def assemble(
    req: ContextRequest,
    svc: ContextService = Depends(_service),
) -> ContextResponse:
    try:
        return svc.assemble(req)
    except IndexNotReadyError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ClaudeNotConfiguredError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=ContextStatus, summary="Context loader configuration status")
def status(svc: ContextService = Depends(_service)) -> ContextStatus:
    return svc.status()
