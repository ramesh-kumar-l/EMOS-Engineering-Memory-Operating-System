# Building a Local-First AI Development Stack from Scratch: FastAPI + FAISS + Next.js

*How I built a production-quality engineering memory system that runs entirely offline — hybrid semantic search, human-gated workflows, Tree-sitter code analysis, and a React Flow knowledge graph. Everything you need to build your own.*

---

Most AI tooling tutorials end at "call the OpenAI API and display the result." That's fine for demos. It's not fine for production systems.

This tutorial goes deeper. I'll walk you through the architecture and key implementation patterns behind EMOS — an open-source engineering memory system — covering:

1. Hybrid semantic search with FAISS + SQLite FTS5
2. Token-budget context assembly with recency decay
3. Human-gated workflow execution
4. Tree-sitter code parsing for repo intelligence
5. A typed Next.js API client that catches backend drift at build time

All of it runs offline. No managed cloud services. No vector database subscription.

Let's build.

---

## The Stack

| Concern | Technology | Why |
|---------|-----------|-----|
| Backend | FastAPI + Uvicorn | Async Python, native ML ecosystem |
| Database | SQLite + FTS5 | Zero server, built-in full-text search |
| Vector search | FAISS (IndexFlatIP) | Local, fast, production-proven |
| Embeddings | sentence-transformers | Offline, no API calls |
| Code parsing | Tree-sitter | CST-level accuracy |
| Frontend | Next.js 16 + App Router | Type-safe, fast |
| UI | Tailwind CSS 4 | Zero config |
| Data fetching | SWR | Cache-aware client fetching |
| Graph | React Flow | Interactive node graphs |

---

## Part 1: Memory Bank — Markdown + SQLite as a Dual-Layer Store

The first insight is the most counterintuitive: **don't use a database as your source of truth.**

EMOS stores all memory documents as Markdown files with YAML frontmatter:

```
memory-bank/
├── architecture.md
├── decisions.md
├── constraints.md
└── lessons.md
```

```markdown
---
slug: decisions
title: Architectural Decisions
category: decisions
tags: [architecture, storage, faiss]
created_at: 2026-05-15T10:00:00Z
updated_at: 2026-05-16T09:00:00Z
---

## ADR-001: Markdown as Primary Memory Storage
**Decision:** All memory documents are stored as Markdown files.
**Rationale:** Human-readable without tooling, git-trackable, AI-readable without transformation.
```

SQLite acts as a **queryable index** over these files. The sync process reads frontmatter and body, inserts/updates the database. If you delete the database, you lose nothing — run sync and it's rebuilt from files.

**Why this matters:** Your engineering memory will outlive any software tool. Markdown in a git repo is readable 30 years from now. A proprietary database format is not.

### SQLite FTS5 with Porter Stemming

For keyword search, EMOS uses a virtual FTS5 table:

```sql
CREATE VIRTUAL TABLE memory_fts USING fts5(
    slug UNINDEXED,
    title,
    content,
    tags,
    tokenize='porter unicode61'
);
```

Porter stemming is the critical addition. Without it, "decided" doesn't match "decisions." With it, `decide`, `decided`, `deciding`, `decision`, `decisions` all match the same root. This is the difference between a search that feels broken and one that feels intelligent.

FastAPI endpoint:

```python
@router.get("/search")
async def search_memory(q: str, limit: int = 20, db: Session = Depends(get_db)):
    results = db.execute(
        text("""
            SELECT slug, title, category, snippet(memory_fts, 2, '<mark>', '</mark>', '...', 32)
            FROM memory_fts
            WHERE memory_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """),
        {"query": q, "limit": limit}
    ).fetchall()
    return {"documents": results, "total": len(results)}
```

The `snippet()` function returns highlighted excerpts with surrounding context — exactly what you need for search result previews.

---

## Part 2: Hybrid Semantic Search — FAISS + FTS5 Fusion

Keyword search fails on semantic queries. If a user asks "why did we choose this storage approach," FTS5 won't match a document that says "the rationale for selecting FAISS was its offline operation model."

The fix: add a vector search layer and fuse the results.

### Generating Embeddings Locally

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # 80MB, downloads once, cached
```

For each document, concatenate title + content and encode:

```python
def embed(texts: list[str]) -> np.ndarray:
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.astype("float32")
```

L2-normalization is critical. With normalized vectors, inner product search (IndexFlatIP) is equivalent to cosine similarity — which is what you want for semantic similarity.

### Building the FAISS Index

```python
import faiss
import json

def build_index(documents: list[dict], index_path: str, meta_path: str):
    texts = [f"{doc['title']} {doc['content']}" for doc in documents]
    embeddings = embed(texts)

    dim = embeddings.shape[1]  # 384 for all-MiniLM-L6-v2
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, index_path)

    # Persist the position → slug mapping
    meta = [{"slug": doc["slug"], "position": i} for i, doc in enumerate(documents)]
    with open(meta_path, "w") as f:
        json.dump(meta, f)
```

The meta file is essential: FAISS stores vectors by position (0, 1, 2...) but you need to map position 42 back to "slug: decisions". Always persist this mapping alongside the index.

### Hybrid Fusion

```python
def hybrid_search(query: str, alpha: float = 0.5, limit: int = 10):
    # Semantic results
    q_vec = embed([query])
    distances, indices = faiss_index.search(q_vec, limit * 2)
    semantic_hits = {
        meta[idx]["slug"]: float(dist)
        for dist, idx in zip(distances[0], indices[0])
        if idx != -1
    }

    # Keyword results (normalized BM25 from FTS5)
    keyword_hits = run_fts_search(query, limit * 2)

    # Collect all unique slugs
    all_slugs = set(semantic_hits) | set(keyword_hits)

    # Fuse scores
    fused = []
    for slug in all_slugs:
        s_score = semantic_hits.get(slug, 0.0)
        k_score = keyword_hits.get(slug, 0.0)
        final = alpha * s_score + (1 - alpha) * k_score
        fused.append((slug, final))

    fused.sort(key=lambda x: x[1], reverse=True)
    return fused[:limit]
```

Alpha = 0.5 is a good default. Let users tune it — some queries are better served by pure keyword, others by pure semantic. Hybrid handles the ambiguous middle ground.

**503 guard for unbuilt index:**

```python
class IndexNotReadyError(Exception):
    pass

@router.get("/search")
async def search(mode: str = "hybrid"):
    if mode in ("semantic", "hybrid") and not index_is_ready():
        raise HTTPException(503, detail="Vector index not built. POST /retrieval/index first.")
```

Never return an empty result when the real answer is "setup required." Explicit errors beat silent failures.

---

## Part 3: Context Assembly — Token-Budget Packing with Recency Decay

Raw search results aren't a context package. You need to rank them, budget them, and format them for an AI prompt.

### Ranking with Recency Decay

```python
from datetime import datetime, timezone
import math

def rank_chunks(chunks, relevance_weight=0.7, recency_weight=0.3, half_life_days=30.0):
    now = datetime.now(timezone.utc)
    ranked = []
    for chunk in chunks:
        updated = datetime.fromisoformat(chunk["updated_at"]).replace(tzinfo=timezone.utc)
        days_old = (now - updated).total_seconds() / 86400
        recency_score = math.pow(2, -days_old / half_life_days)  # exponential decay

        final = relevance_weight * chunk["relevance_score"] + recency_weight * recency_score
        ranked.append({**chunk, "final_score": final})

    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)
```

The 30-day half-life means a document from 30 days ago has half the recency score of a document from today. A document from 90 days ago has one-eighth. This reflects the real engineering heuristic: recent decisions are more likely to be current than old ones.

### Greedy Token Packing

```python
def pack_context(ranked_chunks, token_budget, chars_per_token=4):
    packed = []
    tokens_used = 0

    for chunk in ranked_chunks:
        chunk_tokens = len(chunk["content"]) // chars_per_token
        if tokens_used + chunk_tokens <= token_budget:
            packed.append(chunk)
            tokens_used += chunk_tokens
        # Don't break here — a smaller later chunk might still fit

    return packed, tokens_used
```

The critical detail: **don't break on the first chunk that doesn't fit.** A high-ranked but large document might not fit, but the next ranked document (smaller) might. Greedy packing without early termination fills the budget more completely.

---

## Part 4: Human-Gated Workflow Engine

This is the most architecturally interesting component because the constraint seems artificial until you understand the reason.

### The Data Model

```python
from dataclasses import dataclass
from enum import Enum

class RunStatus(str, Enum):
    running = "running"
    completed = "completed"
    cancelled = "cancelled"

@dataclass
class WorkflowStep:
    id: str
    name: str
    description: str
    human_gate: bool = True  # Always True in MVP
```

A `WorkflowRun` in SQLite:

```sql
CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    current_step INTEGER NOT NULL DEFAULT 0,
    context TEXT,
    step_outcomes TEXT,  -- JSON array of recorded outcomes
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Advancing a Step

```python
@router.post("/runs/{run_id}/advance")
async def advance_step(run_id: str, body: AdvanceStepRequest, db: Session = Depends(get_db)):
    run = get_run_or_404(db, run_id)

    if run.status != RunStatus.running:
        raise HTTPException(400, detail=f"Run is {run.status}, not running.")

    workflow = get_workflow_definition(run.workflow_id)
    next_step = run.current_step + 1

    # Record the outcome for the completed step
    outcomes = json.loads(run.step_outcomes or "[]")
    outcomes.append({
        "step": run.current_step,
        "outcome": body.outcome,
        "notes": body.notes,
        "completed_at": datetime.utcnow().isoformat()
    })

    if next_step >= len(workflow.steps):
        run.status = RunStatus.completed
    else:
        run.current_step = next_step

    run.step_outcomes = json.dumps(outcomes)
    run.updated_at = datetime.utcnow().isoformat()
    db.commit()
    return run
```

The key property: **this endpoint only fires when a human explicitly calls it.** There are no background tasks, no timers, no triggers. The workflow engine is fully stateless between API calls. All continuity lives in the database. A workflow started on Monday can be advanced on Friday — no in-memory state to lose.

### Why Human Gates Are Empowering, Not Limiting

You might think mandatory human gates make the workflow engine useless for automation. The opposite is true.

A workflow engine's value is **structure and continuity**, not speed. When debugging a production incident, you don't want an AI making decisions at each step — you want a structured process that ensures you characterize the failure correctly, form ranked hypotheses, validate them before acting, and record the root cause for future reference. The human gate ensures each of those steps actually happens rather than being skipped in the heat of the moment.

---

## Part 5: Tree-sitter Repo Intelligence

Regex-based code parsing fails on real-world code. Multiline functions, nested structures, string literals containing code-like patterns — regex gets it wrong regularly. Tree-sitter gets it right.

```python
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

def extract_symbols(source: bytes):
    tree = parser.parse(source)
    symbols = []

    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append({
                    "kind": "function",
                    "name": name_node.text.decode(),
                    "line": node.start_point[0] + 1
                })
        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append({
                    "kind": "class",
                    "name": name_node.text.decode(),
                    "line": node.start_point[0] + 1,
                    "methods": extract_methods(node)
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return symbols
```

### Coupling Risk Detection

Build an import graph, then detect risks:

```python
def detect_risks(import_graph: dict[str, set[str]]) -> list[CouplingRisk]:
    risks = []

    for file, imports in import_graph.items():
        # High fan-out
        if len(imports) >= 10:
            risks.append(CouplingRisk(
                file=file, risk_type="high_fan_out",
                severity="medium", detail=f"{len(imports)} outgoing imports"
            ))

    # High fan-in: count how many files import each file
    fan_in = defaultdict(int)
    for imports in import_graph.values():
        for dep in imports:
            fan_in[dep] += 1

    for file, count in fan_in.items():
        if count >= 8:
            risks.append(CouplingRisk(
                file=file, risk_type="high_fan_in",
                severity="high", detail=f"imported by {count} files"
            ))

    # Circular dependencies: DFS
    risks.extend(find_cycles(import_graph))
    return risks
```

High fan-in is the more dangerous risk. If 12 files import `utils.py` and you change its interface, you break 12 places. The risk detector surfaces these before you find out the hard way.

---

## Part 6: Typed Next.js API Client

The frontend is where backend type drift typically causes silent bugs. A function returns `{ results: [] }` in the backend but the frontend expects `{ hits: [] }` — and you only find out at runtime.

EMOS prevents this with explicit TypeScript interfaces that mirror every Pydantic schema:

```typescript
// lib/types.ts — mirrors backend Pydantic schemas exactly
export interface SearchHit {
  slug: string;
  title: string;
  category: string;
  score: number;
  snippet: string;
}

export interface SearchResponse {
  hits: SearchHit[];
  total: number;
  query: string;
  mode: string;
}
```

The typed fetch wrapper:

```typescript
// lib/api.ts
const BASE = "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const retrievalApi = {
  search: (params: { q: string; mode?: string; limit?: number; alpha?: number }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.mode) q.set("mode", params.mode);
    if (params.limit != null) q.set("limit", String(params.limit));
    if (params.alpha != null) q.set("alpha", String(params.alpha));
    return request<SearchResponse>(`/retrieval/search?${q}`);
  },
  buildIndex: () => request<{ status: string }>("/retrieval/index", { method: "POST" }),
  status: () => request<IndexStatus>("/retrieval/status"),
};
```

If the backend renames `hits` to `results`, `SearchResponse` gets updated and TypeScript immediately flags every usage site in the frontend. The compiler becomes your integration test.

### SWR for Data Fetching

```typescript
"use client";
import useSWR from "swr";
import { retrievalApi } from "@/lib/api";

export default function SearchPage() {
  const { data: status } = useSWR("/retrieval/status", retrievalApi.status);

  // data is typed as IndexStatus | undefined
  // status.ready — TypeScript knows this is boolean
  // status.indexed — TypeScript knows this is number
  return (
    <div>
      {status?.ready
        ? `${status.indexed} documents indexed`
        : "Index not built"}
    </div>
  );
}
```

SWR's key-based deduplication means multiple components on the same page can call `retrievalApi.status` independently — SWR coalesces them into a single network request and shares the cached result.

---

## Part 7: React Flow Memory Graph

The knowledge graph is where the data structure becomes visible. Nodes are documents. Edges connect documents that share tags. The layout algorithm places documents in category rings:

```typescript
function buildGraph(docs: Document[]): { nodes: Node[]; edges: Edge[] } {
  const categoryGroups: Record<string, Document[]> = {};
  docs.forEach((d) => {
    (categoryGroups[d.category] = categoryGroups[d.category] || []).push(d);
  });

  const categories = Object.keys(categoryGroups);
  const radius = Math.max(200, categories.length * 80);
  const edgeSet = new Set<string>();

  categories.forEach((cat, ci) => {
    const angle = (ci / categories.length) * 2 * Math.PI;
    const cx = Math.cos(angle) * radius + radius + 100;
    const cy = Math.sin(angle) * radius + radius + 100;
    const catDocs = categoryGroups[cat];
    const innerR = Math.min(100, catDocs.length * 25 + 40);

    catDocs.forEach((doc, di) => {
      const a = (di / catDocs.length) * 2 * Math.PI;
      // ... add node at (cx + cos(a)*innerR, cy + sin(a)*innerR)

      // Add edges for shared tags
      doc.tags.forEach((tag) => {
        docs.forEach((other) => {
          if (other.slug !== doc.slug && other.tags.includes(tag)) {
            const key = [doc.slug, other.slug].sort().join("__");
            if (!edgeSet.has(key)) {
              edgeSet.add(key);
              // add edge
            }
          }
        });
      });
    });
  });
}
```

The `edgeSet` deduplication is critical: without it you'd get two edges between every pair of documents (one in each direction), doubling the visual noise.

---

## Key Lessons

**1. Dependency injection for everything testable.**
Every service in the backend takes its dependencies as constructor parameters. `MemoryEngine(db_path=..., bank_path=...)`. Tests pass in-memory or temp-path versions. 128 tests, zero infrastructure setup beyond `pytest`.

**2. Explicit errors over empty results.**
`IndexNotReadyError → HTTP 503`. `ClaudeNotConfiguredError → HTTP 400`. `RunNotRunning → HTTP 400`. Users should never wonder why they got zero results — they should get a clear signal about what's missing.

**3. Source of truth and cache are different things.**
Markdown files are the truth. SQLite is the cache. FAISS is the cache. Both can be deleted and regenerated. Design your data layer around what survives tool changes, not what's convenient for queries.

**4. Human gates are a feature, not a limitation.**
In a workflow engine, the human gate is what makes the tool trustworthy. Engineers use tools they trust. They don't trust tools that act autonomously on their behalf.

---

## Getting Started

```bash
git clone <repo>
cd EMOS/backend
python -m venv .venv && .venv/Scripts/activate
pip install -e ".[ml,intel]"
alembic upgrade head
uvicorn backend.main:app --reload

# In another terminal:
cd EMOS/frontend
npm install && npm run dev
```

Open `localhost:3000`. Full API docs at `localhost:8000/docs`.

128 tests: `cd backend && pytest`

---

**GitHub:** [your repo link]

The full project is open source. Issues, PRs, and questions welcome.

*If this was useful, follow for more on local-first AI development, engineering memory systems, and building tools that respect your privacy.*
