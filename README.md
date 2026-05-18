# EMOS — Engineering Memory Operating System

**An offline-first engineering intelligence layer for AI-assisted development.**

EMOS preserves engineering knowledge across sessions, assembles context automatically for AI tools, and guides engineering workflows with human-gated deterministic execution — entirely on your local machine.

> AI assists. Humans govern. Every step.

---

## The Problem

Every AI coding session starts at zero. You spend the first ten minutes re-explaining your architecture, your constraints, and your past decisions — knowledge that took months to build but evaporates at the end of every conversation. EMOS fixes this.

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Memory Bank** | Structured Markdown-based engineering memory — decisions, constraints, lessons, risks |
| **Semantic Search** | Hybrid FAISS + SQLite FTS5 search. Find answers by meaning, not just keywords |
| **Context Assembly** | Token-budget packing with recency decay. Auto-assemble AI context before any session |
| **Prompt Registry** | Versioned prompt templates with parameter substitution and usage tracking |
| **Workflow Engine** | 6 deterministic engineering workflows. Human-gated — nothing executes autonomously |
| **Repo Intelligence** | Tree-sitter code analysis: symbols, coupling risks, circular dependencies |
| **Memory Graph** | Interactive React Flow visualization — nodes = documents, edges = shared tags |

---

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+

```bash
# 1. Clone
git clone <repo-url> EMOS && cd EMOS

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                        # Linux/macOS
pip install -e ".[ml,intel]"
alembic upgrade head
uvicorn backend.main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install && npm run dev
```

Open **http://localhost:3000**. API docs at **http://localhost:8000/docs**.

Full setup guide: [`GETTING_STARTED.md`](GETTING_STARTED.md)

---

## Tech Stack

**Backend:** Python 3.11+ · FastAPI · SQLite + FTS5 · FAISS · sentence-transformers · Tree-sitter · Anthropic SDK

**Frontend:** Next.js 16 · React 19 · Tailwind CSS 4 · React Flow · SWR · TypeScript

**Storage:** Markdown (source of truth) · SQLite (index cache) · FAISS (vector index)

---

## Architecture

```
EMOS/
├── memory-bank/    # Engineering memory — Markdown files (source of truth)
├── backend/        # FastAPI Python backend
│   ├── memory/     # Memory Bank engine (Markdown CRUD + SQLite FTS5)
│   ├── retrieval/  # FAISS + hybrid search
│   ├── context/    # Token-budget context assembly + Claude API
│   ├── prompts/    # Prompt registry + usage tracking
│   ├── workflows/  # Human-gated workflow engine
│   └── repo_intel/ # Tree-sitter code analysis
├── frontend/       # Next.js 16 UI (11 routes)
└── data/           # Runtime SQLite + FAISS indexes (auto-created)
```

**Key design decisions:**
- Markdown is the source of truth; SQLite is a cache. Delete the DB, re-sync, nothing lost.
- FAISS flat index (IndexFlatIP) with cosine similarity — exact search, no approximation, local only.
- Human-gated workflow execution: no step runs without your explicit confirmation.
- Offline-first: all features work without internet. Claude API is opt-in.

---

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Memory Bank (SQLite CRUD + FTS5) | ✅ Complete |
| 2 | Semantic Retrieval (FAISS + hybrid search) | ✅ Complete |
| 3 | Context Assembly (token-budget + Claude API) | ✅ Complete |
| 4 | Prompt Registry + Workflow Engine | ✅ Complete |
| 5 | Repo Intelligence (Tree-sitter) | ✅ Complete |
| 6 | Frontend UI (Next.js 16, 11 routes) | ✅ Complete |

**128/128 backend tests passing. 0 TypeScript errors. 11/11 routes compiled.**

---

## Design Principles

1. **Offline-first** — Works without internet. No required cloud services.
2. **Reliability-first** — Explicit errors over silent failures. Confidence scores on retrieval.
3. **Human-governed** — AI describes steps; humans execute and confirm.
4. **Privacy-preserving** — All data stays on your machine by default.
5. **Maintainable** — Markdown + SQLite + FAISS will be readable in 30 years.

---

## Configuration

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Optional — only for AI context assembly
MEMORY_BANK_PATH=../memory-bank
SQLITE_PATH=../data/emos.db
FAISS_INDEX_PATH=../data/indexes
```

---

## License

MIT

---

*Built to solve a real problem: engineering intelligence that survives sessions, tool switches, and team changes.*
