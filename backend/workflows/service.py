import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .definitions import WORKFLOW_DEFINITIONS, WorkflowDefinition
from .models import WorkflowRun, WorkflowStepRecord
from .schemas import (
    AdvanceStepRequest,
    RunListResponse,
    RunResponse,
    StartRunRequest,
    StepDefResponse,
    StepRecordResponse,
    WorkflowDefListResponse,
    WorkflowDefResponse,
)
from ..core.exceptions import WorkflowInvalidStateError, WorkflowNotFoundError, WorkflowRunNotFoundError

_TERMINAL_STATUSES = {"completed", "cancelled"}


def _def_to_response(wf: WorkflowDefinition) -> WorkflowDefResponse:
    return WorkflowDefResponse(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        step_count=len(wf.steps),
        steps=[
            StepDefResponse(
                index=i,
                name=s.name,
                description=s.description,
                requires_human_approval=s.requires_human_approval,
            )
            for i, s in enumerate(wf.steps)
        ],
    )


def _build_run_response(
    run: WorkflowRun,
    wf: WorkflowDefinition,
    steps: list[WorkflowStepRecord],
) -> RunResponse:
    current_step_name = (
        wf.steps[run.current_step_index].name
        if run.current_step_index < len(wf.steps)
        else None
    )
    return RunResponse(
        id=run.id,
        workflow_id=run.workflow_id,
        workflow_name=wf.name,
        status=run.status,
        current_step_index=run.current_step_index,
        current_step_name=current_step_name,
        total_steps=len(wf.steps),
        context_data=run.context_data or {},
        step_records=[
            StepRecordResponse(
                step_index=s.step_index,
                step_name=s.step_name,
                status=s.status,
                notes=s.notes,
                completed_at=s.completed_at,
            )
            for s in sorted(steps, key=lambda s: s.step_index)
        ],
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_definitions(self) -> WorkflowDefListResponse:
        return WorkflowDefListResponse(
            definitions=[_def_to_response(wf) for wf in WORKFLOW_DEFINITIONS.values()]
        )

    def get_definition(self, workflow_id: str) -> WorkflowDefResponse:
        wf = WORKFLOW_DEFINITIONS.get(workflow_id)
        if not wf:
            raise WorkflowNotFoundError(workflow_id)
        return _def_to_response(wf)

    def start_run(self, req: StartRunRequest) -> RunResponse:
        wf = WORKFLOW_DEFINITIONS.get(req.workflow_id)
        if not wf:
            raise WorkflowNotFoundError(req.workflow_id)

        run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=req.workflow_id,
            status="in_progress",
            current_step_index=0,
            context_data=req.context_data,
        )
        self._db.add(run)
        self._db.flush()

        step_records: list[WorkflowStepRecord] = []
        for i, step in enumerate(wf.steps):
            sr = WorkflowStepRecord(
                id=str(uuid.uuid4()),
                run_id=run.id,
                step_index=i,
                step_name=step.name,
                status="awaiting_human" if i == 0 else "pending",
            )
            self._db.add(sr)
            step_records.append(sr)

        self._db.commit()
        self._db.refresh(run)
        for sr in step_records:
            self._db.refresh(sr)

        return _build_run_response(run, wf, step_records)

    def _load_run(self, run_id: str) -> tuple[WorkflowRun, list[WorkflowStepRecord]]:
        run = self._db.query(WorkflowRun).filter_by(id=run_id).first()
        if not run:
            raise WorkflowRunNotFoundError(run_id)
        steps = self._db.query(WorkflowStepRecord).filter_by(run_id=run_id).all()
        return run, steps

    def get_run(self, run_id: str) -> RunResponse:
        run, steps = self._load_run(run_id)
        return _build_run_response(run, WORKFLOW_DEFINITIONS[run.workflow_id], steps)

    def list_runs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
    ) -> RunListResponse:
        q = self._db.query(WorkflowRun)
        if workflow_id:
            q = q.filter_by(workflow_id=workflow_id)
        if status:
            q = q.filter_by(status=status)
        runs = q.order_by(WorkflowRun.created_at.desc()).all()
        result = []
        for run in runs:
            steps = self._db.query(WorkflowStepRecord).filter_by(run_id=run.id).all()
            result.append(_build_run_response(run, WORKFLOW_DEFINITIONS[run.workflow_id], steps))
        return RunListResponse(runs=result, total=len(result))

    def advance_step(self, run_id: str, req: AdvanceStepRequest) -> RunResponse:
        run, steps = self._load_run(run_id)
        if run.status in _TERMINAL_STATUSES:
            raise WorkflowInvalidStateError(run_id, run.status)

        wf = WORKFLOW_DEFINITIONS[run.workflow_id]
        now = datetime.now(timezone.utc)

        current_sr = next((s for s in steps if s.step_index == run.current_step_index), None)
        if current_sr:
            current_sr.status = "skipped" if req.skip else "completed"
            current_sr.notes = req.notes
            current_sr.completed_at = now

        if req.context_data:
            merged = dict(run.context_data or {})
            merged.update(req.context_data)
            run.context_data = merged

        next_index = run.current_step_index + 1
        if next_index >= len(wf.steps):
            run.status = "completed"
        else:
            run.current_step_index = next_index
            next_sr = next((s for s in steps if s.step_index == next_index), None)
            if next_sr:
                next_sr.status = "awaiting_human"

        run.updated_at = now
        self._db.commit()
        self._db.refresh(run)
        for s in steps:
            self._db.refresh(s)

        return _build_run_response(run, wf, steps)

    def cancel_run(self, run_id: str) -> RunResponse:
        run, steps = self._load_run(run_id)
        if run.status in _TERMINAL_STATUSES:
            raise WorkflowInvalidStateError(run_id, run.status)
        run.status = "cancelled"
        run.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(run)
        return _build_run_response(run, WORKFLOW_DEFINITIONS[run.workflow_id], steps)
