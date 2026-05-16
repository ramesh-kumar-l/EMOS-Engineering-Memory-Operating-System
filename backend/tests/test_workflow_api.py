from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from ..api.v1.memory import get_mem_engine
from ..core.database import get_db
from ..main import app
from ..memory.engine import MemoryBankEngine
from ..workflows.definitions import WORKFLOW_DEFINITIONS
import pytest


@pytest.fixture
def workflow_client(tmp_db, mem_engine: MemoryBankEngine) -> TestClient:
    Factory = sessionmaker(bind=tmp_db)

    def _override_db():
        session = Factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_mem_engine] = lambda: mem_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Definitions ───────────────────────────────────────────────────────────────

def test_list_definitions_returns_all(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/definitions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["definitions"]
    ids = {d["id"] for d in data["definitions"]}
    assert ids == set(WORKFLOW_DEFINITIONS.keys())


def test_get_definition_wf001(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/definitions/WF-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "WF-001"
    assert data["name"] == "Architecture Review"
    assert data["step_count"] == len(WORKFLOW_DEFINITIONS["WF-001"].steps)
    assert len(data["steps"]) == data["step_count"]


def test_get_nonexistent_definition_returns_404(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/definitions/WF-999")
    assert resp.status_code == 404


def test_definition_steps_have_required_fields(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/definitions/WF-002")
    assert resp.status_code == 200
    step = resp.json()["steps"][0]
    assert "index" in step
    assert "name" in step
    assert "description" in step
    assert "requires_human_approval" in step


# ── Start run ─────────────────────────────────────────────────────────────────

def test_start_run(workflow_client: TestClient) -> None:
    resp = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["workflow_id"] == "WF-001"
    assert data["status"] == "in_progress"
    assert data["current_step_index"] == 0
    assert data["total_steps"] == len(WORKFLOW_DEFINITIONS["WF-001"].steps)


def test_start_run_creates_step_records(workflow_client: TestClient) -> None:
    resp = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-003"})
    assert resp.status_code == 201
    data = resp.json()
    steps = data["step_records"]
    assert len(steps) == data["total_steps"]
    # First step awaiting human, rest pending
    assert steps[0]["status"] == "awaiting_human"
    assert all(s["status"] == "pending" for s in steps[1:])


def test_start_run_with_context_data(workflow_client: TestClient) -> None:
    resp = workflow_client.post("/api/v1/workflows/runs", json={
        "workflow_id": "WF-002",
        "context_data": {"ticket": "JIRA-123", "component": "auth"},
    })
    assert resp.status_code == 201
    assert resp.json()["context_data"] == {"ticket": "JIRA-123", "component": "auth"}


def test_start_run_invalid_workflow_returns_404(workflow_client: TestClient) -> None:
    resp = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-999"})
    assert resp.status_code == 404


# ── Get / list runs ───────────────────────────────────────────────────────────

def test_get_run(workflow_client: TestClient) -> None:
    create_resp = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-004"})
    run_id = create_resp.json()["id"]
    resp = workflow_client.get(f"/api/v1/workflows/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == run_id


def test_get_nonexistent_run_returns_404(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/runs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_runs_empty(workflow_client: TestClient) -> None:
    resp = workflow_client.get("/api/v1/workflows/runs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_runs(workflow_client: TestClient) -> None:
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-002"})
    resp = workflow_client.get("/api/v1/workflows/runs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_runs_filter_by_workflow(workflow_client: TestClient) -> None:
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-002"})
    resp = workflow_client.get("/api/v1/workflows/runs?workflow_id=WF-001")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_runs_filter_by_status(workflow_client: TestClient) -> None:
    r1 = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    run_id = r1.json()["id"]
    workflow_client.post(f"/api/v1/workflows/runs/{run_id}/cancel")
    workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-002"})

    resp = workflow_client.get("/api/v1/workflows/runs?status=cancelled")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── Advance step ──────────────────────────────────────────────────────────────

def test_advance_step_moves_to_next(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    run_id = r.json()["id"]
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step_index"] == 1
    assert data["step_records"][0]["status"] == "completed"
    assert data["step_records"][1]["status"] == "awaiting_human"


def test_advance_step_with_notes(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    run_id = r.json()["id"]
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={
        "notes": "Architecture looks solid."
    })
    assert resp.status_code == 200
    assert resp.json()["step_records"][0]["notes"] == "Architecture looks solid."


def test_advance_step_skip(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    run_id = r.json()["id"]
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={"skip": True})
    assert resp.status_code == 200
    assert resp.json()["step_records"][0]["status"] == "skipped"


def test_advance_step_merges_context(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={
        "workflow_id": "WF-001",
        "context_data": {"existing": "value"},
    })
    run_id = r.json()["id"]
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={
        "context_data": {"new_key": "new_value"}
    })
    assert resp.status_code == 200
    ctx = resp.json()["context_data"]
    assert ctx["existing"] == "value"
    assert ctx["new_key"] == "new_value"


def test_advance_all_steps_completes_run(workflow_client: TestClient) -> None:
    # Use WF-005 (5 steps — shortest workflow)
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-005"})
    run_id = r.json()["id"]
    total = r.json()["total_steps"]
    for _ in range(total):
        workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={})
    final = workflow_client.get(f"/api/v1/workflows/runs/{run_id}")
    assert final.json()["status"] == "completed"


def test_advance_nonexistent_run_returns_404(workflow_client: TestClient) -> None:
    resp = workflow_client.post(
        "/api/v1/workflows/runs/00000000-0000-0000-0000-000000000000/advance", json={}
    )
    assert resp.status_code == 404


def test_advance_completed_run_returns_409(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-005"})
    run_id = r.json()["id"]
    total = r.json()["total_steps"]
    for _ in range(total):
        workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={})
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={})
    assert resp.status_code == 409


# ── Cancel ────────────────────────────────────────────────────────────────────

def test_cancel_run(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-001"})
    run_id = r.json()["id"]
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_completed_run_returns_409(workflow_client: TestClient) -> None:
    r = workflow_client.post("/api/v1/workflows/runs", json={"workflow_id": "WF-005"})
    run_id = r.json()["id"]
    total = r.json()["total_steps"]
    for _ in range(total):
        workflow_client.post(f"/api/v1/workflows/runs/{run_id}/advance", json={})
    resp = workflow_client.post(f"/api/v1/workflows/runs/{run_id}/cancel")
    assert resp.status_code == 409


def test_cancel_nonexistent_run_returns_404(workflow_client: TestClient) -> None:
    resp = workflow_client.post(
        "/api/v1/workflows/runs/00000000-0000-0000-0000-000000000000/cancel"
    )
    assert resp.status_code == 404
