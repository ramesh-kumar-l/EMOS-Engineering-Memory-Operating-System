from datetime import datetime
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    template_body: str = Field(..., min_length=1)
    category: str = "general"


class TemplateUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    template_body: str | None = None
    category: str | None = None


class TemplateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    slug: str
    title: str
    description: str
    template_body: str
    parameters: list[str]
    category: str
    version: int
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]
    total: int


class RenderRequest(BaseModel):
    parameters: dict[str, str] = {}
    log_usage: bool = False
    workflow_run_id: str | None = None


class RenderResponse(BaseModel):
    slug: str
    version: int
    rendered: str
    parameters_used: dict[str, str]
    missing_parameters: list[str] = []
    usage_id: str | None = None


class UsageCreate(BaseModel):
    parameters_used: dict[str, str] = {}
    rendered_prompt: str = ""
    workflow_run_id: str | None = None
    outcome: str | None = None
    notes: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class UsageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    template_slug: str
    rendered_prompt: str
    parameters_used: dict
    workflow_run_id: str | None
    outcome: str | None
    notes: str | None
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime


class UsageListResponse(BaseModel):
    usages: list[UsageResponse]
    total: int
