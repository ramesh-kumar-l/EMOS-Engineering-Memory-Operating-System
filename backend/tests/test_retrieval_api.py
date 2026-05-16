from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from ..api.v1.memory import get_mem_engine
from ..api.v1.retrieval import get_embedder, get_faiss_index
from ..core.database import get_db
from ..main import app
from ..retrieval.index import FAISSIndex


class _MockEmbedder:
    """Fixed-output embedder — no model download, deterministic for tests."""

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


@pytest.fixture
def retrieval_client(tmp_path: Path, tmp_db, mem_engine) -> TestClient:
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

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_status_empty(retrieval_client: TestClient) -> None:
    resp = retrieval_client.get("/api/v1/retrieval/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_indexed"] == 0
    assert data["total_documents"] == 0


def test_build_index_no_docs(retrieval_client: TestClient) -> None:
    resp = retrieval_client.post("/api/v1/retrieval/index")
    assert resp.status_code == 200
    assert resp.json()["indexed"] == 0


def test_semantic_search_without_index_returns_503(retrieval_client: TestClient) -> None:
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "test", "mode": "semantic"})
    assert resp.status_code == 503


def test_hybrid_search_without_index_returns_503(retrieval_client: TestClient) -> None:
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "test", "mode": "hybrid"})
    assert resp.status_code == 503


def test_keyword_search_works_without_index(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "kw-doc", "title": "Keyword Test", "content": "unique keyword phrase"
    })
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "keyword", "mode": "keyword"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "keyword"


def test_build_and_status(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "s1", "title": "Doc One", "content": "first document content"
    })
    retrieval_client.post("/api/v1/memory", json={
        "slug": "s2", "title": "Doc Two", "content": "second document content"
    })
    resp = retrieval_client.post("/api/v1/retrieval/index")
    assert resp.status_code == 200
    assert resp.json()["indexed"] == 2

    status = retrieval_client.get("/api/v1/retrieval/status").json()
    assert status["total_indexed"] == 2
    assert status["total_documents"] == 2


def test_keyword_search_returns_relevant_doc(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "arch-doc", "title": "Architecture Overview",
        "content": "system architecture and design patterns", "category": "architecture"
    })
    retrieval_client.post("/api/v1/memory", json={
        "slug": "unrelated", "title": "Unrelated", "content": "cooking recipes"
    })
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "architecture", "mode": "keyword"})
    assert resp.status_code == 200
    slugs = [r["slug"] for r in resp.json()["items"]]
    assert "arch-doc" in slugs


def test_semantic_search_after_build(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "sem-doc", "title": "Semantic Doc", "content": "embedding and vector search"
    })
    retrieval_client.post("/api/v1/retrieval/index")
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "vectors", "mode": "semantic"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["semantic_score"] is not None
    assert data["items"][0]["keyword_score"] is None


def test_hybrid_search_after_build(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "hyb-doc", "title": "Hybrid Doc", "content": "hybrid search combines methods"
    })
    retrieval_client.post("/api/v1/retrieval/index")
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "hybrid", "mode": "hybrid"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "hybrid"


def test_search_response_has_preview(retrieval_client: TestClient) -> None:
    retrieval_client.post("/api/v1/memory", json={
        "slug": "preview-doc", "title": "Preview", "content": "preview content text here"
    })
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "preview", "mode": "keyword"})
    item = resp.json()["items"][0]
    assert "content_preview" in item
    assert len(item["content_preview"]) <= 200


def test_limit_parameter(retrieval_client: TestClient) -> None:
    for i in range(5):
        retrieval_client.post("/api/v1/memory", json={
            "slug": f"limit-doc-{i}", "title": f"Limit Doc {i}", "content": f"limit test document {i}"
        })
    retrieval_client.post("/api/v1/retrieval/index")
    resp = retrieval_client.get("/api/v1/retrieval/search", params={"q": "limit", "mode": "keyword", "limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 2
