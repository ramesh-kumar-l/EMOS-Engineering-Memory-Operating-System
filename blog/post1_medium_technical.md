# I Built an Offline-First Engineering Memory OS — Architecture, Decisions, and What I Learned

*A technical deep-dive into EMOS: local FAISS semantic search, human-gated workflow engines, Tree-sitter repo analysis, and token-budget context assembly — all without a cloud dependency.*

---

Every time I start a new AI coding session, I spend the first ten minutes explaining the same things:

> "We're offline-first. We chose FastAPI because of the ML stack. We rejected ChromaDB because it adds server complexity. The token budget is capped at 80K to leave headroom for the response."

The AI listens. I get useful help. I end the session.

Next session: I start over from scratch.

This is the fundamental flaw in how we use AI for engineering work today. **The tools are stateless. The intelligence is disposable.** Every context window is a goldfish bowl — useful for exactly one swim and then empty.

So I built EMOS — the Engineering Memory Operating System. An offline-first local system that persists engineering intelligence, assembles context automatically, and guides engineering workflows without autonomous execution. Six implementation phases. 128 passing tests. A full Next.js 16 UI.

This is the technical story of how I built it.

---

## The Architecture Constraint That Shaped Everything

Before writing a single line of code, I committed to one hard constraint:

**Offline-first. No required cloud services. All data local by default.**

This wasn't a feature. It was a forcing function that eliminated entire categories of architectural choices.

- No Pinecone (cloud-only vector DB)
- No managed Postgres (external server required)
- No ChromaDB (adds its own server process)
- No Firebase, no Supabase, no anything-as-a-service

The result: **Markdown + SQLite + FAISS**. Three technologies that run anywhere, require no server process beyond the app itself, and produce human-readable artifacts that survive indefinitely.

### Why Markdown as the Source of Truth

Every memory document is a Markdown file with YAML frontmatter:

```markdown
---
slug: architecture-decisions
title: Architectural Decisions
category: decisions
tags: [architecture, storage, faiss, offline]
created_at: 2026-05-15T10:00:00Z
updated_at: 2026-05-16T09:30:00Z
---

## ADR-001: Markdown as Primary Memory Storage
**Decision:** All memory bank documents are stored as Markdown files...
```

SQLite is a *cache* over this. When you edit a file directly, you click "Sync" and the database catches up. If you delete the database, you lose nothing — it's fully reconstructible from the Markdown files.

This is ADR-001 in the project's own memory bank: **"SQLite is a cache; Markdown is the source of truth."** The key reason: Markdown is git-trackable, AI-readable without transformation, and survives any tool change. You can `cat` a memory document with no tooling at all.

---

## Phase 1: Memory Bank — CRUD on Top of Markdown + SQLite FTS5

The Memory Bank engine reads and writes YAML-fronted Markdown and maintains a SQLite index for fast querying.

The SQLite schema uses **FTS5 with the Porter stemmer**:

```sql
CREATE VIRTUAL TABLE memory_fts USING fts5(
    slug UNINDEXED,
    title,
    content,
    tags,
    tokenize='porter unicode61'
);
```

Porter stemming means searching for "decision" also matches "decisions", "decided", "deciding". This is the difference between a search that feels like a tool and one that feels like a toy.

The FastAPI endpoint for search:

```
GET /api/v1/memory/search?q=offline+storage&limit=20
```

Returns documents ranked by BM25 relevance score from FTS5. Sub-100ms on 10,000 documents. Zero dependencies beyond SQLite, which is in Python's standard library.

**Test coverage:** 21 unit + integration tests. The engine is injected via dependency injection so tests can override the database path — no test touches production data.

---

## Phase 2: Semantic Retrieval — FAISS + sentence-transformers

Full-text search is fast but brittle. If you search for "why did we pick this vector store", FTS5 won't match a document that says "the rationale for choosing FAISS was its local-only operation model."

Semantic search fixes this.

**Embedding model:** `all-MiniLM-L6-v2` from sentence-transformers. 80MB download on first use, cached locally forever. Produces 384-dimension vectors. Runs on CPU — no GPU required.

**Vector index:** `faiss.IndexFlatIP` — inner product similarity over L2-normalized vectors, which is equivalent to cosine similarity. Flat index is exact (no approximation), which is correct for up to ~50,000 documents. Beyond that, switch to `IndexIVFFlat` for sub-linear query time.

Index persistence:
```
data/indexes/memory.faiss         # binary FAISS index
data/indexes/memory_meta.json     # slug → position mapping
```

The meta file is critical: FAISS stores vectors by position, not by ID. The mapping lets you translate "position 42 in the index" back to "slug: architecture-decisions".

**Hybrid search fusion:**

Neither pure semantic nor pure keyword dominates across all query types. The hybrid mode fuses both:

```python
final_score = alpha * semantic_score + (1 - alpha) * keyword_score
```

Where `alpha` is user-configurable (0–1). Default 0.5. Results are re-ranked by the fused score.

This is the same approach used in production retrieval systems like Elasticsearch's reciprocal rank fusion. The difference is: this one runs entirely locally.

**IndexNotReadyError:** Before the index is built, any request to `/retrieval/search?mode=semantic` or `mode=hybrid` returns HTTP 503 with a clear error message. No silent failure, no empty results — an explicit signal that setup is required.

---

## Phase 3: Context Assembly — Token-Budget Packing with Recency Decay

Semantic search gives you ranked documents. Context assembly turns them into a Claude-ready context package within a token budget.

The ranking function:

```python
final_score = relevance_score * (1 - recency_weight) + recency_score * recency_weight

# Recency score: exponential decay with 30-day half-life
recency_score = 2 ** (-days_since_update / 30.0)
```

A document that's highly relevant but two years old scores lower than a slightly less relevant document from last week. This reflects real engineering intuition: recent constraints and recent decisions are more likely to be current than old ones.

**Greedy packing:**

Chunks are sorted by final score descending, then packed greedily:

```python
packed = []
tokens_used = 0
for chunk in ranked_chunks:
    if tokens_used + chunk.tokens <= budget:
        packed.append(chunk)
        tokens_used += chunk.tokens
    # Don't break — a smaller later chunk might still fit
```

Token counting uses a `~4 chars/token` heuristic (standard for Claude models). For production accuracy, use `tiktoken` or the Anthropic SDK's token counter.

**Claude API integration:** The `ClaudeClient` wraps the Anthropic SDK and is lazy-imported — it's only loaded if `ANTHROPIC_API_KEY` is set. If the key is absent, the `/context/assemble` endpoint still works and returns the assembled context text. Only the "send to Claude" path returns `ClaudeNotConfiguredError → HTTP 400`. Offline-first holds.

---

## Phase 4: Prompt Registry + Workflow Engine

### Prompt Registry

Prompt templates are stored in SQLite with `{parameter}` placeholder syntax. Parameters are auto-detected via regex:

```python
import re
PARAM_RE = re.compile(r'\{(\w+)\}')
parameters = PARAM_RE.findall(template_content)
```

Every edit auto-increments `version`. Usage is tracked per-invocation: parameters used, outcome, token counts, workflow link. This turns prompts from sticky notes into engineering assets.

### Workflow Engine

Six hardcoded workflow definitions (Architecture Review, Implementation, Debugging, Evaluation, Documentation, Release Preparation). Each is a list of `WorkflowStep` dataclasses:

```python
@dataclass
class WorkflowStep:
    id: str
    name: str
    description: str
    human_gate: bool  # always True in MVP
```

The execution model: a `WorkflowRun` in SQLite tracks `current_step`, `status`, and per-step outcomes. The only way to advance is `POST /workflows/runs/{id}/advance` with a human-provided outcome. There is no timer, no trigger, no background task. The engine is fully stateless between API calls — all state lives in the database.

This is ADR-004: **"No workflow step executes autonomously."** The AI describes what should happen at each step. The human does the work and records the result. The workflow provides structure and continuity — not automation.

---

## Phase 5: Repo Intelligence — Tree-sitter AST at Scale

Tree-sitter is a parser generator that produces concrete syntax trees (CSTs) for 40+ languages. Unlike regex-based parsing, it handles real-world code correctly — nested structures, multiline expressions, edge cases.

EMOS uses three Tree-sitter grammars:
- `tree-sitter-python` — `.py` files
- `tree-sitter-javascript` — `.js`, `.jsx` files
- `tree-sitter-typescript` — `.ts`, `.tsx` files

For each file, the analyzer extracts:
- Function definitions (with line numbers)
- Class definitions (with methods)
- Import statements (for coupling analysis)

**Coupling risk detection:**

```python
# High fan-out: this file depends on too many things
if len(file_imports) >= 10:
    risks.append(CouplingRisk(
        file=path,
        risk_type="high_fan_out",
        severity="medium",
        detail=f"{len(file_imports)} imports detected"
    ))

# Circular dependency: DFS on the import graph
def detect_cycles(graph: dict[str, set[str]]) -> list[tuple]:
    ...  # standard DFS with visited/stack tracking
```

High fan-in (≥8 files importing from one file) catches bottleneck modules — the ones where a refactor breaks everything. Circular dependencies catch the deadlock risk that manifests as import errors at runtime.

Repo intelligence is **stateless** — no database persistence. Analysis runs on demand and returns results directly. This is a deliberate choice: a point-in-time snapshot is more honest than a stale persisted analysis.

---

## Phase 6: Frontend — Next.js 16 + React Flow

The UI is a dark-themed single-page application built on Next.js 16.2.6 with App Router, Tailwind CSS 4, and SWR for data fetching.

**Typed API client:** A single `lib/api.ts` module exports per-domain objects (`memoryApi`, `retrievalApi`, `contextApi`, etc.) wrapping a typed `fetch` helper:

```typescript
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { ... });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
```

All interfaces in `lib/types.ts` mirror the Pydantic schemas in the backend exactly. TypeScript strict mode catches any drift at build time.

**React Flow graph:** The memory graph builds nodes from documents and edges from shared tags:

```typescript
function buildGraph(docs: Document[]): { nodes: Node[]; edges: Edge[] } {
  // Group documents by category
  // Position categories in outer ring (radius = categories.length * 80)
  // Position documents within category in inner ring
  // Draw edge between any two documents sharing a tag (deduped)
}
```

The visual result: a galaxy-like layout where related documents cluster together and cross-category connections are visible across the graph.

**Build result:** 0 TypeScript errors. 11/11 routes compiled. Turbopack.

---

## What I'd Do Differently

**1. FAISS metadata coupling.** The `memory_meta.json` → FAISS position mapping requires keeping the two files in sync. If the meta file gets corrupted or out of date with the index, search silently returns wrong results. I'd replace this with a SQLite-backed vector store that keeps metadata and vectors in the same transaction boundary.

**2. Token counting.** The `~4 chars/token` heuristic is fast but inaccurate for code-heavy content where density varies significantly. Adding `anthropic.count_tokens()` as an optional accurate path would improve context assembly quality.

**3. Workflow definitions as data, not code.** Hardcoded Python dataclasses work, but a YAML-based workflow definition file would let users add custom workflows without touching backend code.

---

## What Worked Remarkably Well

**Markdown as source of truth** was the right call. Every memory document is inspectable with `cat`. Every document is in git history. The database is ephemeral; the knowledge is permanent.

**Dependency injection for testing.** Every service takes its dependencies as constructor parameters. Tests inject fake/test versions. 128 tests, zero flaky ones, no mocking of network calls.

**Human-gated workflows.** The constraint of "AI describes, human executes, human records" is actually empowering. The workflow engine's job is to provide structure and continuity — not to do the work. This turns out to be exactly the right abstraction for AI-assisted engineering.

---

## Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | FastAPI | 0.136.1 |
| ASGI server | Uvicorn | 0.47.0 |
| Data validation | Pydantic v2 | 2.13.4 |
| ORM + migrations | SQLAlchemy 2 + Alembic | 2.0.49 / 1.18.4 |
| Full-text search | SQLite FTS5 | built-in |
| Vector search | FAISS | 1.13.2 |
| Embeddings | sentence-transformers | 5.5.0 |
| Code parsing | Tree-sitter | 0.25.2 |
| AI client | Anthropic SDK | 0.40.0 |
| Frontend | Next.js 16 + React 19 | 16.2.6 / 19.2.4 |
| Styling | Tailwind CSS | v4 |
| Graph viz | React Flow | 11.11.4 |
| Data fetching | SWR | 2.4.1 |

---

The project is open source. If you've ever started an AI session by re-explaining your architecture for the fifth time this week, EMOS is for you.

**GitHub:** [link to your repo]

*Next post: the UX decisions behind building a workflow engine that engineers will actually use.*
