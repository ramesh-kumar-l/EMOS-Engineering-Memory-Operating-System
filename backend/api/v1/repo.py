from fastapi import APIRouter, Query

from ...core.exceptions import RepoInvalidPathError, RepoPathNotFoundError, to_http
from ...repo_intel.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DocsRequest,
    DocsResponse,
    RisksResponse,
    SymbolsResponse,
)
from ...repo_intel.service import RepoIntelService

router = APIRouter(prefix="/repo", tags=["repo"])
_svc = RepoIntelService()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return _svc.analyze(req)
    except (RepoPathNotFoundError, RepoInvalidPathError) as exc:
        raise to_http(exc)


@router.get("/symbols", response_model=SymbolsResponse)
def symbols(file: str = Query(..., description="Absolute or relative path to source file")) -> SymbolsResponse:
    try:
        return _svc.symbols(file)
    except (RepoPathNotFoundError, RepoInvalidPathError) as exc:
        raise to_http(exc)


@router.post("/risks", response_model=RisksResponse)
def risks(req: AnalyzeRequest) -> RisksResponse:
    try:
        return _svc.risks(req)
    except (RepoPathNotFoundError, RepoInvalidPathError) as exc:
        raise to_http(exc)


@router.post("/docs", response_model=DocsResponse)
def generate_docs(req: DocsRequest) -> DocsResponse:
    try:
        return _svc.generate_docs(req)
    except (RepoPathNotFoundError, RepoInvalidPathError) as exc:
        raise to_http(exc)
