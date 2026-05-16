from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get(client: TestClient) -> None:
    r = client.post("/api/v1/memory", json={
        "slug": "test-doc",
        "title": "Test Document",
        "content": "This is test content.",
        "category": "general",
        "tags": ["test"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["slug"] == "test-doc"
    assert data["title"] == "Test Document"
    assert data["word_count"] == 4

    r2 = client.get("/api/v1/memory/test-doc")
    assert r2.status_code == 200
    assert r2.json()["content"] == "This is test content."


def test_create_duplicate_returns_409(client: TestClient) -> None:
    payload = {"slug": "dup-doc", "title": "Dup", "content": "x"}
    client.post("/api/v1/memory", json=payload)
    r = client.post("/api/v1/memory", json=payload)
    assert r.status_code == 409


def test_get_missing_returns_404(client: TestClient) -> None:
    r = client.get("/api/v1/memory/no-such-doc")
    assert r.status_code == 404


def test_update_document(client: TestClient) -> None:
    client.post("/api/v1/memory", json={"slug": "upd-doc", "title": "Old", "content": "old"})
    r = client.put("/api/v1/memory/upd-doc", json={"title": "New", "content": "new content"})
    assert r.status_code == 200
    assert r.json()["title"] == "New"
    assert r.json()["content"] == "new content"


def test_delete_document(client: TestClient) -> None:
    client.post("/api/v1/memory", json={"slug": "del-doc", "title": "Del", "content": "bye"})
    r = client.delete("/api/v1/memory/del-doc")
    assert r.status_code == 204
    assert client.get("/api/v1/memory/del-doc").status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    r = client.delete("/api/v1/memory/ghost")
    assert r.status_code == 404


def test_list_documents(client: TestClient) -> None:
    client.post("/api/v1/memory", json={"slug": "doc-a", "title": "A", "content": "a", "category": "core"})
    client.post("/api/v1/memory", json={"slug": "doc-b", "title": "B", "content": "b", "category": "log"})
    r = client.get("/api/v1/memory")
    assert r.status_code == 200
    assert r.json()["total"] >= 2


def test_list_filter_by_category(client: TestClient) -> None:
    client.post("/api/v1/memory", json={"slug": "cat-a", "title": "A", "content": "a", "category": "core"})
    client.post("/api/v1/memory", json={"slug": "cat-b", "title": "B", "content": "b", "category": "log"})
    r = client.get("/api/v1/memory?category=core")
    assert r.status_code == 200
    slugs = [d["slug"] for d in r.json()["items"]]
    assert "cat-a" in slugs
    assert "cat-b" not in slugs


def test_fts_search(client: TestClient) -> None:
    client.post("/api/v1/memory", json={
        "slug": "search-doc",
        "title": "Searchable Document",
        "content": "This document contains the keyword elephant.",
    })
    r = client.get("/api/v1/memory/search?q=elephant")
    assert r.status_code == 200
    slugs = [d["slug"] for d in r.json()["items"]]
    assert "search-doc" in slugs


def test_invalid_slug_rejected(client: TestClient) -> None:
    r = client.post("/api/v1/memory", json={"slug": "INVALID SLUG!", "title": "X", "content": "x"})
    assert r.status_code == 422
