from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.exceptions import WorkflowInvalidStateError, WorkflowNotFoundError, WorkflowRunNotFoundError
from ...workflows.schemas import (
    AdvanceStepRequest,
    RunListResponse,
    RunResponse,
    StartRunRequest,
    WorkflowDefListResponse,
    WorkflowDefResponse,
)
from ...workflows.service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _svc(db: Session = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)


@router.get("/definitions", response_model=WorkflowDefListResponse, summary="List all workflow definitions")
def list_definitions(svc: WorkflowService = Depends(_svc)) -> WorkflowDefListResponse:
    return svc.list_definitions()


@router.get("/definitions/{workflow_id}", response_model=WorkflowDefResponse, summary="Get a workflow definition")
def get_definition(workflow_id: str, svc: WorkflowService = Depends(_svc)) -> WorkflowDefResponse:
    try:
        return svc.get_definition(workflow_id)
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs", response_model=RunResponse, status_code=201, summary="Start a workflow run")
def start_run(req: StartRunRequest, svc: WorkflowService = Depends(_svc)) -> RunResponse:
    try:
        return svc.start_run(req)
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs", response_model=RunListResponse, summary="List workflow runs")
def list_runs(
    workflow_id: str | None = Query(None),
    status: str | None = Query(None),
    svc: WorkflowService = Depends(_svc),
) -> RunListResponse:
    return svc.list_runs(workflow_id=workflow_id, status=status)


@router.get("/runs/{run_id}", response_model=RunResponse, summary="Get a workflow run")
def get_run(run_id: str, svc: WorkflowService = Depends(_svc)) -> RunResponse:
    try:
        return svc.get_run(run_id)
    except WorkflowRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/advance", response_model=RunResponse, summary="Advance the current workflow step")
def advance_step(run_id: str, req: AdvanceStepRequest, svc: WorkflowService = Depends(_svc)) -> RunResponse:
    try:
        return svc.advance_step(run_id, req)
    except WorkflowRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkflowInvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/runs/{run_id}/cancel", response_model=RunResponse, summary="Cancel a workflow run")
def cancel_run(run_id: str, svc: WorkflowService = Depends(_svc)) -> RunResponse:
    try:
        return svc.cancel_run(run_id)
    except WorkflowRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkflowInvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
