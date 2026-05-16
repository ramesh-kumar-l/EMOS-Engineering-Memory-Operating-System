from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.exceptions import PromptAlreadyExistsError, PromptNotFoundError, PromptRenderError
from ...prompts.schemas import (
    RenderRequest,
    RenderResponse,
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
    UsageCreate,
    UsageListResponse,
    UsageResponse,
)
from ...prompts.service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _svc(db: Session = Depends(get_db)) -> PromptService:
    return PromptService(db)


@router.get("", response_model=TemplateListResponse, summary="List all prompt templates")
def list_templates(
    category: str | None = Query(None),
    svc: PromptService = Depends(_svc),
) -> TemplateListResponse:
    return svc.list_all(category=category)


@router.post("", response_model=TemplateResponse, status_code=201, summary="Create a prompt template")
def create_template(req: TemplateCreate, svc: PromptService = Depends(_svc)) -> TemplateResponse:
    try:
        return svc.create(req)
    except PromptAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{slug}", response_model=TemplateResponse, summary="Get a prompt template")
def get_template(slug: str, svc: PromptService = Depends(_svc)) -> TemplateResponse:
    try:
        return svc.get(slug)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{slug}", response_model=TemplateResponse, summary="Update a prompt template")
def update_template(slug: str, req: TemplateUpdate, svc: PromptService = Depends(_svc)) -> TemplateResponse:
    try:
        return svc.update(slug, req)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{slug}", status_code=204, summary="Delete a prompt template")
def delete_template(slug: str, svc: PromptService = Depends(_svc)) -> None:
    try:
        svc.delete(slug)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{slug}/render", response_model=RenderResponse, summary="Render a prompt template with parameters")
def render_template(slug: str, req: RenderRequest, svc: PromptService = Depends(_svc)) -> RenderResponse:
    try:
        return svc.render(slug, req)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PromptRenderError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{slug}/usage", response_model=UsageResponse, status_code=201, summary="Log a prompt usage record")
def log_usage(slug: str, req: UsageCreate, svc: PromptService = Depends(_svc)) -> UsageResponse:
    try:
        return svc.log_usage(slug, req)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{slug}/usage", response_model=UsageListResponse, summary="Get prompt usage history")
def get_usage(
    slug: str,
    limit: int = Query(50, ge=1, le=500),
    svc: PromptService = Depends(_svc),
) -> UsageListResponse:
    return svc.get_usage(slug, limit=limit)
