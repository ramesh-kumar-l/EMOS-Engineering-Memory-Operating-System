import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import PromptTemplate, PromptUsage
from .schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    RenderRequest,
    RenderResponse,
    UsageCreate,
    UsageResponse,
    UsageListResponse,
)
from ..core.exceptions import PromptNotFoundError, PromptAlreadyExistsError, PromptRenderError

_PARAM_RE = re.compile(r"\{(\w+)\}")


def _extract_params(body: str) -> list[str]:
    return sorted(set(_PARAM_RE.findall(body)))


def _to_response(t: PromptTemplate) -> TemplateResponse:
    return TemplateResponse.model_validate(t)


class PromptService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, req: TemplateCreate) -> TemplateResponse:
        if self._db.query(PromptTemplate).filter_by(slug=req.slug).first():
            raise PromptAlreadyExistsError(req.slug)
        params = _extract_params(req.template_body)
        tmpl = PromptTemplate(
            id=str(uuid.uuid4()),
            slug=req.slug,
            title=req.title,
            description=req.description,
            template_body=req.template_body,
            parameters=params,
            category=req.category,
            version=1,
        )
        self._db.add(tmpl)
        self._db.commit()
        self._db.refresh(tmpl)
        return _to_response(tmpl)

    def get(self, slug: str) -> TemplateResponse:
        tmpl = self._db.query(PromptTemplate).filter_by(slug=slug).first()
        if not tmpl:
            raise PromptNotFoundError(slug)
        return _to_response(tmpl)

    def list_all(self, category: str | None = None) -> TemplateListResponse:
        q = self._db.query(PromptTemplate)
        if category:
            q = q.filter_by(category=category)
        results = q.order_by(PromptTemplate.updated_at.desc()).all()
        return TemplateListResponse(
            templates=[_to_response(t) for t in results],
            total=len(results),
        )

    def update(self, slug: str, req: TemplateUpdate) -> TemplateResponse:
        tmpl = self._db.query(PromptTemplate).filter_by(slug=slug).first()
        if not tmpl:
            raise PromptNotFoundError(slug)
        if req.title is not None:
            tmpl.title = req.title
        if req.description is not None:
            tmpl.description = req.description
        if req.template_body is not None:
            tmpl.template_body = req.template_body
            tmpl.parameters = _extract_params(req.template_body)
        if req.category is not None:
            tmpl.category = req.category
        tmpl.version += 1
        tmpl.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(tmpl)
        return _to_response(tmpl)

    def delete(self, slug: str) -> None:
        tmpl = self._db.query(PromptTemplate).filter_by(slug=slug).first()
        if not tmpl:
            raise PromptNotFoundError(slug)
        self._db.delete(tmpl)
        self._db.commit()

    def render(self, slug: str, req: RenderRequest) -> RenderResponse:
        tmpl = self._db.query(PromptTemplate).filter_by(slug=slug).first()
        if not tmpl:
            raise PromptNotFoundError(slug)

        missing = [p for p in tmpl.parameters if p not in req.parameters]
        if missing:
            raise PromptRenderError(missing)

        def _replace(match: re.Match) -> str:
            return req.parameters.get(match.group(1), match.group(0))

        rendered = _PARAM_RE.sub(_replace, tmpl.template_body)

        usage_id = None
        if req.log_usage:
            usage = PromptUsage(
                id=str(uuid.uuid4()),
                template_slug=slug,
                rendered_prompt=rendered,
                parameters_used=req.parameters,
                workflow_run_id=req.workflow_run_id,
            )
            self._db.add(usage)
            self._db.commit()
            usage_id = usage.id

        return RenderResponse(
            slug=slug,
            version=tmpl.version,
            rendered=rendered,
            parameters_used=req.parameters,
            usage_id=usage_id,
        )

    def log_usage(self, slug: str, req: UsageCreate) -> UsageResponse:
        if not self._db.query(PromptTemplate).filter_by(slug=slug).first():
            raise PromptNotFoundError(slug)
        usage = PromptUsage(
            id=str(uuid.uuid4()),
            template_slug=slug,
            rendered_prompt=req.rendered_prompt,
            parameters_used=req.parameters_used,
            workflow_run_id=req.workflow_run_id,
            outcome=req.outcome,
            notes=req.notes,
            input_tokens=req.input_tokens,
            output_tokens=req.output_tokens,
        )
        self._db.add(usage)
        self._db.commit()
        self._db.refresh(usage)
        return UsageResponse.model_validate(usage)

    def get_usage(self, slug: str, limit: int = 50) -> UsageListResponse:
        rows = (
            self._db.query(PromptUsage)
            .filter_by(template_slug=slug)
            .order_by(PromptUsage.created_at.desc())
            .limit(limit)
            .all()
        )
        return UsageListResponse(
            usages=[UsageResponse.model_validate(r) for r in rows],
            total=len(rows),
        )
