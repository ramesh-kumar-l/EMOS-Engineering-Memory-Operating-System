from datetime import datetime
from pydantic import BaseModel, Field


class StepDefResponse(BaseModel):
    index: int
    name: str
    description: str
    requires_human_approval: bool


class WorkflowDefResponse(BaseModel):
    id: str
    name: str
    description: str
    step_count: int
    steps: list[StepDefResponse]


class WorkflowDefListResponse(BaseModel):
    definitions: list[WorkflowDefResponse]


class StartRunRequest(BaseModel):
    workflow_id: str = Field(..., description="e.g. WF-001")
    context_data: dict = {}


class AdvanceStepRequest(BaseModel):
    notes: str | None = None
    context_data: dict | None = None
    skip: bool = False


class StepRecordResponse(BaseModel):
    model_config = {"from_attributes": True}

    step_index: int
    step_name: str
    status: str
    notes: str | None
    completed_at: datetime | None


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: str
    current_step_index: int
    current_step_name: str | None
    total_steps: int
    context_data: dict
    step_records: list[StepRecordResponse]
    created_at: datetime
    updated_at: datetime


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
