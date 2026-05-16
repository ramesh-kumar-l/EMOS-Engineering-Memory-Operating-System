"""Integration tests for Phase 5 — Repo Intelligence."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ..main import app


@pytest.fixture(scope="module")
def repo_client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "main.py").write_text(
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "from .utils import helper\n"
        "\n"
        "def main():\n"
        "    pass\n"
        "\n"
        "def parse_args():\n"
        "    pass\n"
        "\n"
        "class App:\n"
        "    def run(self):\n"
        "        pass\n"
        "    def stop(self):\n"
        "        pass\n"
    )
    (tmp_path / "utils.py").write_text(
        "import os\n"
        "from .models import User\n"
        "\n"
        "def helper(x):\n"
        "    return x\n"
        "\n"
        "def format_date(d):\n"
        "    return str(d)\n"
    )
    (tmp_path / "models.py").write_text(
        "class User:\n"
        "    def __init__(self, name):\n"
        "        self.name = name\n"
        "\n"
        "class Session:\n"
        "    pass\n"
    )
    return tmp_path


# ── Analyze ───────────────────────────────────────────────────────────────────

def test_analyze_returns_all_files(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(sample_repo)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_files"] == 3


def test_analyze_counts_symbols(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(sample_repo)})
    assert resp.json()["total_symbols"] > 0


def test_analyze_file_summary_function_count(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(sample_repo)})
    summaries = {s["path"]: s for s in resp.json()["file_summaries"]}
    assert summaries["main.py"]["function_count"] == 2
    assert summaries["main.py"]["class_count"] == 1


def test_analyze_file_summary_imports(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(sample_repo)})
    summaries = {s["path"]: s for s in resp.json()["file_summaries"]}
    imports = summaries["main.py"]["imports"]
    assert "os" in imports
    assert "sys" in imports
    assert "pathlib" in imports


def test_analyze_respects_max_files(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(sample_repo), "max_files": 1})
    assert resp.status_code == 200
    assert resp.json()["total_files"] == 1


def test_analyze_extension_filter(repo_client: TestClient, sample_repo: Path) -> None:
    # Add a JS file to the repo
    (sample_repo / "app.js").write_text("function greet() {}\n")
    resp = repo_client.post(
        "/api/v1/repo/analyze",
        json={"path": str(sample_repo), "extensions": [".js"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_files"] == 1
    assert data["file_summaries"][0]["language"] == "javascript"


def test_analyze_nonexistent_path_returns_404(repo_client: TestClient) -> None:
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": "/nonexistent/path/xyz"})
    assert resp.status_code == 404


def test_analyze_file_path_returns_400(repo_client: TestClient, tmp_path: Path) -> None:
    f = tmp_path / "solo.py"
    f.write_text("x = 1\n")
    resp = repo_client.post("/api/v1/repo/analyze", json={"path": str(f)})
    assert resp.status_code == 400


# ── Symbols ───────────────────────────────────────────────────────────────────

def test_symbols_returns_functions_and_classes(repo_client: TestClient, sample_repo: Path) -> None:
    f = sample_repo / "main.py"
    resp = repo_client.get(f"/api/v1/repo/symbols?file={f}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "python"
    names = {s["name"] for s in data["symbols"]}
    assert "main" in names
    assert "parse_args" in names
    assert "App" in names


def test_symbols_class_methods_populated(repo_client: TestClient, sample_repo: Path) -> None:
    f = sample_repo / "main.py"
    resp = repo_client.get(f"/api/v1/repo/symbols?file={f}")
    syms = {s["name"]: s for s in resp.json()["symbols"]}
    assert "App" in syms
    assert set(syms["App"]["methods"]) == {"run", "stop"}


def test_symbols_line_numbers_positive(repo_client: TestClient, sample_repo: Path) -> None:
    f = sample_repo / "main.py"
    resp = repo_client.get(f"/api/v1/repo/symbols?file={f}")
    for sym in resp.json()["symbols"]:
        assert sym["line"] >= 1


def test_symbols_nonexistent_file_returns_404(repo_client: TestClient) -> None:
    resp = repo_client.get("/api/v1/repo/symbols?file=/nonexistent/file.py")
    assert resp.status_code == 404


def test_symbols_unsupported_extension_returns_400(repo_client: TestClient, tmp_path: Path) -> None:
    f = tmp_path / "data.csv"
    f.write_text("col1,col2\n1,2\n")
    resp = repo_client.get(f"/api/v1/repo/symbols?file={f}")
    assert resp.status_code == 400


def test_symbols_javascript_file(repo_client: TestClient, tmp_path: Path) -> None:
    f = tmp_path / "app.js"
    f.write_text(
        "import React from 'react';\n"
        "function App() { return null; }\n"
        "class Widget { render() {} }\n"
    )
    resp = repo_client.get(f"/api/v1/repo/symbols?file={f}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "javascript"
    names = {s["name"] for s in data["symbols"]}
    assert "App" in names
    assert "Widget" in names


# ── Risks ─────────────────────────────────────────────────────────────────────

def test_risks_detects_high_fan_out(repo_client: TestClient, tmp_path: Path) -> None:
    # 12 imports → medium/high fan-out
    body = "\n".join(f"import mod{i}" for i in range(12)) + "\n"
    (tmp_path / "fat.py").write_text(body)
    resp = repo_client.post("/api/v1/repo/risks", json={"path": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_count"] > 0
    types = {r["risk_type"] for r in data["risks"]}
    assert "high_fan_out" in types


def test_risks_clean_repo_no_risks(repo_client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "simple.py").write_text("import os\ndef foo(): pass\n")
    resp = repo_client.post("/api/v1/repo/risks", json={"path": str(tmp_path)})
    assert resp.status_code == 200
    assert resp.json()["risk_count"] == 0


def test_risks_response_has_severity(repo_client: TestClient, tmp_path: Path) -> None:
    body = "\n".join(f"import mod{i}" for i in range(12)) + "\n"
    (tmp_path / "fat.py").write_text(body)
    resp = repo_client.post("/api/v1/repo/risks", json={"path": str(tmp_path)})
    for risk in resp.json()["risks"]:
        assert risk["severity"] in ("low", "medium", "high")


def test_risks_nonexistent_path_returns_404(repo_client: TestClient) -> None:
    resp = repo_client.post("/api/v1/repo/risks", json={"path": "/nonexistent"})
    assert resp.status_code == 404


def test_risks_file_path_returns_400(repo_client: TestClient, tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("pass\n")
    resp = repo_client.post("/api/v1/repo/risks", json={"path": str(f)})
    assert resp.status_code == 400


# ── Docs ──────────────────────────────────────────────────────────────────────

def test_docs_returns_markdown(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/docs", json={"path": str(sample_repo), "title": "Test Repo"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Repo"
    assert "# Test Repo" in data["markdown"]


def test_docs_includes_file_index(repo_client: TestClient, sample_repo: Path) -> None:
    resp = repo_client.post("/api/v1/repo/docs", json={"path": str(sample_repo), "title": "T"})
    md = resp.json()["markdown"]
    assert "main.py" in md
    assert "utils.py" in md


def test_docs_default_title_uses_dir_name(repo_client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def f(): pass\n")
    resp = repo_client.post("/api/v1/repo/docs", json={"path": str(tmp_path)})
    assert resp.status_code == 200
    assert resp.json()["title"] == tmp_path.name


def test_docs_nonexistent_path_returns_404(repo_client: TestClient) -> None:
    resp = repo_client.post("/api/v1/repo/docs", json={"path": "/nonexistent"})
    assert resp.status_code == 404
