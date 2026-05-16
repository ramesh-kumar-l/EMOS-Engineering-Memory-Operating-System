from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from ..api.v1.context import get_claude_client
from ..api.v1.memory import get_mem_engine
from ..api.v1.retrieval import get_embedder, get_faiss_index
from ..context.client import AIClient
from ..core.database import get_db
from ..main import app
from ..retrieval.index import FAISSIndex


class _MockEmbedder:
    DIM = 16

    def encode(self, texts: list[str]) -> np.ndarray:
        rng = np.random.default_rng(42)
        vecs = rng.random((len(texts), self.DIM), dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        return self.DIM


class _MockClaudeClient:
    model = "claude-mock-1"
    _response: str = "Mock Claude response."

    def complete(self, system: str, user_prompt: str, max_tokens: int = 4096) -> tuple[str, int, int]:
        return self._response, len(system) // 4, len(self._response) // 4


def _make_context_client(
    tmp_path: Path, tmp_db, mem_engine, claude_override: AIClient | None = None
) -> TestClient:
    Factory = sessionmaker(bind=tmp_db)

    def _override_db():
        session = Factory()
        try:
            yield session
        finally:
            session.close()

    embedder = _MockEmbedder()
    index = FAISSIndex(tmp_path / "indexes")

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_mem_engine] = lambda: mem_engine
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_faiss_index] = lambda: index
    app.dependency_overrides[get_claude_client] = lambda: claude_override

    return TestClient(app)


@pytest.fixture
def context_client(tmp_path: Path, tmp_db, mem_engine) -> TestClient:
    client = _make_context_client(tmp_path, tmp_db, mem_engine, claude_override=None)
    with client as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def context_client_with_claude(tmp_path: Path, tmp_db, mem_engine) -> TestClient:
    client = _make_context_client(tmp_path, tmp_db, mem_engine, claude_override=_MockClaudeClient())
    with client as c:
        yield c
    app.dependency_overrides.clear()


# ── Status endpoint ───────────────────────────────────────────────────────────

def test_status_no_claude(context_client: TestClient) -> None:
    resp = context_client.get("/api/v1/context/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["claude_configured"] is False
    assert data["model"] is None
    assert data["token_budget"] > 0


def test_status_with_claude(context_client_with_claude: TestClient) -> None:
    resp = context_client_with_claude.get("/api/v1/context/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["claude_configured"] is True
    assert data["model"] == "claude-mock-1"


# ── Assemble endpoint ─────────────────────────────────────────────────────────

def test_assemble_empty_memory_bank(context_client: TestClient) -> None:
    resp = context_client.post("/api/v1/context/assemble", json={"query": "anything", "mode": "keyword"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["package"]["chunks"] == []
    assert data["package"]["total_tokens"] == 0
    assert data["claude_response"] is None


def test_assemble_keyword_mode_returns_relevant_chunks(context_client: TestClient) -> None:
    context_client.post("/api/v1/memory", json={
        "slug": "arch-doc", "title": "Architecture Guide",
        "content": "This document describes the system architecture in detail.", "category": "architecture"
    })
    context_client.post("/api/v1/memory", json={
        "slug": "unrelated", "title": "Recipes", "content": "How to bake bread."
    })
    resp = context_client.post("/api/v1/context/assemble", json={"query": "architecture", "mode": "keyword"})
    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()["package"]["chunks"]]
    assert "arch-doc" in slugs


def test_assemble_package_has_scores(context_client: TestClient) -> None:
    context_client.post("/api/v1/memory", json={
        "slug": "scored-doc", "title": "Scored", "content": "scoring and ranking content"
    })
    resp = context_client.post("/api/v1/context/assemble", json={"query": "scoring", "mode": "keyword"})
    assert resp.status_code == 200
    chunk = resp.json()["package"]["chunks"][0]
    assert "relevance_score" in chunk
    assert "recency_score" in chunk
    assert "final_score" in chunk
    assert chunk["token_count"] > 0


def test_assemble_token_budget_respected(context_client: TestClient) -> None:
    long_content = "word " * 2000  # ~10000 chars → ~2500 tokens
    context_client.post("/api/v1/memory", json={
        "slug": "long-doc", "title": "Long Doc", "content": long_content
    })
    # Set a small budget
    resp = context_client.post("/api/v1/context/assemble", json={
        "query": "word", "mode": "keyword", "token_budget": 1_000
    })
    assert resp.status_code == 200
    pkg = resp.json()["package"]
    assert pkg["total_tokens"] <= 1_000


def test_assemble_max_chunks_respected(context_client: TestClient) -> None:
    for i in range(10):
        context_client.post("/api/v1/memory", json={
            "slug": f"chunk-doc-{i}", "title": f"Doc {i}", "content": f"content document {i}"
        })
    resp = context_client.post("/api/v1/context/assemble", json={
        "query": "content", "mode": "keyword", "max_chunks": 3
    })
    assert resp.status_code == 200
    assert len(resp.json()["package"]["chunks"]) <= 3


def test_assemble_budget_used_pct_correct(context_client: TestClient) -> None:
    context_client.post("/api/v1/memory", json={
        "slug": "pct-doc", "title": "Pct", "content": "test content"
    })
    resp = context_client.post("/api/v1/context/assemble", json={
        "query": "test", "mode": "keyword", "token_budget": 80_000
    })
    assert resp.status_code == 200
    pkg = resp.json()["package"]
    expected_pct = round(pkg["total_tokens"] / 80_000 * 100, 1)
    assert abs(pkg["budget_used_pct"] - expected_pct) < 0.1


def test_assemble_send_to_claude_no_key_returns_400(context_client: TestClient) -> None:
    resp = context_client.post("/api/v1/context/assemble", json={
        "query": "test", "mode": "keyword", "send_to_claude": True
    })
    assert resp.status_code == 400
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]


def test_assemble_send_to_claude_with_key(context_client_with_claude: TestClient) -> None:
    context_client_with_claude.post("/api/v1/memory", json={
        "slug": "claude-doc", "title": "Claude Test", "content": "AI memory system"
    })
    resp = context_client_with_claude.post("/api/v1/context/assemble", json={
        "query": "AI memory",
        "mode": "keyword",
        "send_to_claude": True,
        "claude_prompt": "Summarise what EMOS does.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["claude_response"] == "Mock Claude response."
    assert data["model"] == "claude-mock-1"
    assert data["input_tokens"] is not None
    assert data["output_tokens"] is not None


def test_assemble_semantic_without_index_returns_503(context_client: TestClient) -> None:
    resp = context_client.post("/api/v1/context/assemble", json={"query": "test", "mode": "semantic"})
    assert resp.status_code == 503


def test_assemble_recency_weight_zero_uses_only_relevance(context_client: TestClient) -> None:
    context_client.post("/api/v1/memory", json={
        "slug": "rel-doc", "title": "Relevant", "content": "relevant unique phrase here"
    })
    resp = context_client.post("/api/v1/context/assemble", json={
        "query": "relevant unique phrase", "mode": "keyword", "recency_weight": 0.0
    })
    assert resp.status_code == 200
    chunks = resp.json()["package"]["chunks"]
    if chunks:
        # final_score should equal relevance_score when recency_weight=0
        chunk = chunks[0]
        assert abs(chunk["final_score"] - chunk["relevance_score"]) < 0.01
