from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from ..api.v1.memory import get_mem_engine
from ..core.database import get_db
from ..main import app
from ..memory.engine import MemoryBankEngine


@pytest.fixture
def prompt_client(tmp_db, mem_engine: MemoryBankEngine) -> TestClient:
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


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_empty(prompt_client: TestClient) -> None:
    resp = prompt_client.get("/api/v1/prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["templates"] == []
    assert data["total"] == 0


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_template(prompt_client: TestClient) -> None:
    resp = prompt_client.post("/api/v1/prompts", json={
        "slug": "hello-world",
        "title": "Hello World",
        "template_body": "Hello, {name}! Welcome to {place}.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "hello-world"
    assert data["version"] == 1
    assert sorted(data["parameters"]) == ["name", "place"]


def test_create_duplicate_returns_409(prompt_client: TestClient) -> None:
    body = {"slug": "dup", "title": "Dup", "template_body": "Hello {x}"}
    prompt_client.post("/api/v1/prompts", json=body)
    resp = prompt_client.post("/api/v1/prompts", json=body)
    assert resp.status_code == 409


def test_create_no_params(prompt_client: TestClient) -> None:
    resp = prompt_client.post("/api/v1/prompts", json={
        "slug": "static", "title": "Static", "template_body": "No parameters here."
    })
    assert resp.status_code == 201
    assert resp.json()["parameters"] == []


# ── Get ───────────────────────────────────────────────────────────────────────

def test_get_template(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "get-me", "title": "Get Me", "template_body": "Value: {val}"
    })
    resp = prompt_client.get("/api/v1/prompts/get-me")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "get-me"


def test_get_nonexistent_returns_404(prompt_client: TestClient) -> None:
    resp = prompt_client.get("/api/v1/prompts/does-not-exist")
    assert resp.status_code == 404


# ── List with filter ──────────────────────────────────────────────────────────

def test_list_filter_by_category(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "cat-a", "title": "Cat A", "template_body": "A", "category": "alpha"
    })
    prompt_client.post("/api/v1/prompts", json={
        "slug": "cat-b", "title": "Cat B", "template_body": "B", "category": "beta"
    })
    resp = prompt_client.get("/api/v1/prompts?category=alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["templates"][0]["slug"] == "cat-a"


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_bumps_version(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "bump-me", "title": "Old Title", "template_body": "Hello {x}"
    })
    resp = prompt_client.put("/api/v1/prompts/bump-me", json={"title": "New Title"})
    assert resp.status_code == 200
    assert resp.json()["version"] == 2
    assert resp.json()["title"] == "New Title"


def test_update_template_body_re_extracts_params(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "param-change", "title": "T", "template_body": "Hello {old_param}"
    })
    resp = prompt_client.put("/api/v1/prompts/param-change", json={
        "template_body": "Hi {new_param1} and {new_param2}"
    })
    assert resp.status_code == 200
    assert sorted(resp.json()["parameters"]) == ["new_param1", "new_param2"]


def test_update_nonexistent_returns_404(prompt_client: TestClient) -> None:
    resp = prompt_client.put("/api/v1/prompts/no-such-slug", json={"title": "X"})
    assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_template(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "bye", "title": "Bye", "template_body": "Farewell"
    })
    resp = prompt_client.delete("/api/v1/prompts/bye")
    assert resp.status_code == 204
    assert prompt_client.get("/api/v1/prompts/bye").status_code == 404


def test_delete_nonexistent_returns_404(prompt_client: TestClient) -> None:
    assert prompt_client.delete("/api/v1/prompts/ghost").status_code == 404


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_substitutes_params(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "greet", "title": "Greet", "template_body": "Hello, {name}! You are {age} years old."
    })
    resp = prompt_client.post("/api/v1/prompts/greet/render", json={
        "parameters": {"name": "Alice", "age": "30"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["rendered"] == "Hello, Alice! You are 30 years old."
    assert data["usage_id"] is None


def test_render_missing_param_returns_422(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "strict", "title": "Strict", "template_body": "Hi {required_param}"
    })
    resp = prompt_client.post("/api/v1/prompts/strict/render", json={"parameters": {}})
    assert resp.status_code == 422
    assert "required_param" in resp.json()["detail"]


def test_render_logs_usage_when_flag_set(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "logged", "title": "Logged", "template_body": "Hi {name}"
    })
    resp = prompt_client.post("/api/v1/prompts/logged/render", json={
        "parameters": {"name": "Bob"},
        "log_usage": True,
    })
    assert resp.status_code == 200
    assert resp.json()["usage_id"] is not None


def test_render_nonexistent_returns_404(prompt_client: TestClient) -> None:
    resp = prompt_client.post("/api/v1/prompts/no-template/render", json={"parameters": {}})
    assert resp.status_code == 404


# ── Usage ─────────────────────────────────────────────────────────────────────

def test_log_usage(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "usage-tmpl", "title": "Usage Tmpl", "template_body": "Run {task}"
    })
    resp = prompt_client.post("/api/v1/prompts/usage-tmpl/usage", json={
        "parameters_used": {"task": "review"},
        "rendered_prompt": "Run review",
        "outcome": "success",
        "input_tokens": 100,
        "output_tokens": 200,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["outcome"] == "success"
    assert data["input_tokens"] == 100


def test_get_usage_history(prompt_client: TestClient) -> None:
    prompt_client.post("/api/v1/prompts", json={
        "slug": "hist-tmpl", "title": "Hist", "template_body": "Do {thing}"
    })
    for i in range(3):
        prompt_client.post("/api/v1/prompts/hist-tmpl/usage", json={
            "rendered_prompt": f"Do thing{i}"
        })
    resp = prompt_client.get("/api/v1/prompts/hist-tmpl/usage")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


def test_log_usage_nonexistent_template_returns_404(prompt_client: TestClient) -> None:
    resp = prompt_client.post("/api/v1/prompts/no-tmpl/usage", json={})
    assert resp.status_code == 404
