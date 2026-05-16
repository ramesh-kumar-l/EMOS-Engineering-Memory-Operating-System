# EMOS Roadmap

## Phase 0 — Foundation ✅ COMPLETE
**Goal:** Establish memory bank, architecture docs, and project scaffold.

- [x] Define vision and product philosophy
- [x] Define MVP boundary
- [x] Define system architecture
- [x] Scaffold memory bank (all 15 documents)
- [x] Scaffold project directory structure
- [x] Validate local environment (Python 3.14.4, pydantic 2.13, SQLAlchemy 2.0 — all confirmed)
- Note: faiss-cpu + sentence-transformers Python 3.14 wheel status unvalidated (Phase 2 task)

## Phase 1 — Memory Bank Backend ✅ COMPLETE
**Goal:** Working local memory bank with CRUD and SQLite indexing.

- [x] FastAPI project scaffold (backend/, pyproject.toml, alembic.ini)
- [x] Memory Bank engine (Markdown read/write with YAML frontmatter)
- [x] SQLite schema and Alembic migrations
- [x] REST API: /memory endpoints (CRUD + /search + /sync)
- [x] Full-text search (SQLite FTS5 with Porter stemmer)
- [x] Unit + integration tests (21/21 passing)
- [x] Dependency injection pattern (engine overridable for testing)

## Phase 2 — Semantic Retrieval ✅ COMPLETE
**Goal:** Hybrid search over memory bank content.

- [x] sentence-transformers integration (all-MiniLM-L6-v2, lazy-loading, offline-first)
- [x] FAISS flat index builder (IndexFlatIP — cosine similarity over L2-normalised vectors)
- [x] Index persistence to disk (data/indexes/memory.faiss + memory_meta.json)
- [x] Hybrid search (BM25 FTS5 + FAISS cosine fusion, configurable alpha)
- [x] REST API: GET /retrieval/search, POST /retrieval/index, GET /retrieval/status
- [x] IndexNotReadyError (503) guard for semantic/hybrid before index is built
- [x] 19 tests passing (8 engine + 11 API integration)
- Note: faiss-cpu 1.13.2 + sentence-transformers 5.5.0 both have Python 3.14 wheels — no sub-venv needed

## Phase 3 — Claude Context Loader ✅ COMPLETE
**Goal:** Assemble token-efficient context packages for AI sessions.

- [x] Context assembly engine (ContextService — greedy token-budget packing)
- [x] Token budget management (configurable per-request, 1K–200K; ~4 chars/token heuristic)
- [x] Chunk ranking (relevance + recency decay, 30-day half-life, configurable weight)
- [x] Claude API integration (ClaudeClient + AIClient protocol for test injection)
- [x] REST API: POST /context/assemble, GET /context/status
- [x] ClaudeNotConfiguredError → HTTP 400 (explicit, not silent)
- [x] 22 tests passing (10 ranker unit + 12 API integration)
- Note: anthropic SDK lazy-imported inside ClaudeClient to keep startup fast

## Phase 4 — Prompt Registry + Workflow Engine ✅ COMPLETE
**Goal:** Reusable, versioned prompts and deterministic workflows.

- [x] Prompt template system (SQLite-backed; {param} substitution; auto-extracts parameters)
- [x] Prompt versioning (auto-increments on every update)
- [x] Prompt usage tracking (SQLite: parameters, outcome, token counts, workflow link)
- [x] Workflow definitions (6 workflows from memory-bank/workflows.md, hardcoded as Python dataclasses)
- [x] Workflow execution engine (human-step-gated; stateful runs in SQLite; advance/skip/cancel)
- [x] REST API: /prompts (CRUD + render + usage), /workflows (definitions + runs lifecycle)
- [x] Shared SQLAlchemy Base (backend/core/base.py — all models unified; Alembic migration 002)
- [x] 43 new tests (22 prompt + 21 workflow); 105/105 total passing

## Phase 5 — Repo Intelligence + Documentation Engine ✅ COMPLETE
**Goal:** Lightweight repo analysis and automated documentation generation.

- [x] Tree-sitter integration (tree-sitter 0.25.2 + tree-sitter-python + tree-sitter-javascript; handles .py, .js, .ts, .jsx, .tsx)
- [x] Repo structure analyzer (directory walk; extracts functions, classes, methods, imports per file)
- [x] Coupling and dependency risk detector (high fan-out ≥10, high fan-in ≥8, circular dependency DFS)
- [x] Documentation generator (Markdown: overview table, language breakdown, file index with symbols)
- [x] REST API: POST /repo/analyze, GET /repo/symbols, POST /repo/risks, POST /repo/docs
- [x] 23 tests passing; 128/128 total passing
- Note: No new DB tables — repo intel is stateless (analysis on demand, no persistence)

## Phase 6 — Frontend UI ✅ COMPLETE
**Goal:** Usable local web interface for all EMOS capabilities.

- [x] Next.js 16 project scaffold (TypeScript + Tailwind CSS + App Router)
- [x] Navigation sidebar with active-state highlighting
- [x] Dashboard with live stat cards (memory count, index status, active runs)
- [x] Memory bank browser (list, search by FTS, filter by category, sync from disk)
- [x] Document viewer + full create/edit/delete with Markdown content editor
- [x] Semantic search UI (hybrid/semantic/keyword modes, index build trigger)
- [x] Context assembly UI (token budget slider, alpha control, chunk viewer, copy context)
- [x] Prompt registry UI (list, create, edit, render with parameter inputs, usage history)
- [x] Workflow execution UI (definitions list, start run, step advancement, cancel, progress bar)
- [x] Workflow run detail page (step-by-step human-gate UI with outcome + notes)
- [x] Repo intelligence UI (analyze, risks with severity badges, docs with copy markdown)
- [x] React Flow graph visualization (memory relationship graph via shared tags, node inspector)
- [x] Typed API client covering all 7 backend module groups (30+ endpoints)
- [x] Build: 0 TypeScript errors, 11/11 routes compile (Next.js 16.2.6 Turbopack)

## Deferred (Post-MVP)
- Cloud sync (opt-in)
- Multi-user collaboration
- Plugin system
- IDE extension
- Local LLM abstraction layer (Ollama etc.)
