# EMOS Architecture

## System Overview

EMOS is structured as a local-first monorepo with a clear separation between backend services, frontend UI, and the memory layer.

```
EMOS/
├── memory-bank/          # Engineering memory (this directory)
├── backend/              # FastAPI Python backend
│   ├── api/              # Route handlers
│   ├── core/             # Business logic
│   ├── memory/           # Memory Bank engine
│   ├── retrieval/        # Semantic retrieval (FAISS)
│   ├── repo_intel/       # Repository intelligence (Tree-sitter)
│   ├── reliability/      # Reliability + hallucination guards
│   └── prompts/          # Prompt registry
├── frontend/             # Next.js + React + Tailwind
│   ├── pages/
│   ├── components/
│   └── lib/
└── data/                 # Local SQLite + FAISS indexes
```

## Component Boundaries

### Memory Bank Engine
- Reads and writes structured Markdown files
- Maintains index in SQLite (fast lookups)
- No cloud dependency
- Source of truth: Markdown files; SQLite is a cache

### Semantic Retrieval Engine
- FAISS vector index over memory bank + repo content
- sentence-transformers for local embedding generation
- Hybrid search: keyword (SQLite FTS) + semantic (FAISS)
- Incremental indexing: only re-index changed files

### Claude Context Loader
- Assembles context packages from memory bank
- Applies token budget constraints before sending to Claude API
- Ranks retrieved chunks by relevance + recency
- Outputs structured context payloads

### Prompt Registry
- Stores prompt templates as versioned Markdown
- Supports parameterized templates
- Tracks usage history and outcomes in SQLite

### Workflow Engine
- Deterministic workflow definitions in YAML
- Supported workflows: architecture-review, implementation, debug, evaluation, documentation, release-prep
- No autonomous execution; human approval required at each step

### Reliability Layer
- Validates all AI-generated outputs against known facts
- Flags hallucination risks (invented APIs, fabricated dependencies)
- Assigns confidence scores to retrieval results
- Maintains reliability-status.md

### Repo Intelligence Layer
- Tree-sitter parsing for structure analysis
- Infers architectural patterns from file layout
- Detects coupling and dependency risks
- Does not modify repo files

### Documentation Engine
- Generates Markdown documentation from structured data
- Templates for: architecture, setup, workflows, changelogs
- All output is human-readable and AI-readable

## Data Flow

```
User Query
    │
    ▼
Context Loader ──────► Memory Bank (Markdown + SQLite)
    │                        │
    │                        ▼
    │               Semantic Retrieval (FAISS)
    │                        │
    ▼                        ▼
Reliability Layer ◄──── Ranked Chunks
    │
    ▼
Claude API (with assembled context)
    │
    ▼
Reliability Validation
    │
    ▼
Response + Memory Update
```

## Storage Strategy

| Data Type         | Storage       | Reason                          |
|-------------------|---------------|---------------------------------|
| Memory documents  | Markdown      | Human-readable, git-trackable   |
| Indexes / lookups | SQLite        | Fast queries, zero server       |
| Vector embeddings | FAISS         | Local, no cloud dependency      |
| Prompt templates  | Markdown      | Versionable, readable           |
| Config            | YAML/TOML     | Simple, editable                |

## API Design

REST API via FastAPI. All endpoints are local-only by default.

Key endpoint groups:
- `/memory` — CRUD for memory bank documents
- `/retrieval` — semantic + keyword search
- `/context` — context assembly for AI sessions
- `/prompts` — prompt registry management
- `/workflows` — workflow execution and status
- `/reliability` — reliability checks and confidence scores
- `/repo` — repository intelligence queries

## Reliability Strategy

- Memory Bank is the ground truth; AI outputs are validated against it
- Confidence scores accompany all retrieval results
- Hallucination risk flags are surfaced to the user, never silently suppressed
- No AI output is written to memory without human confirmation

## Scalability Assumptions

- Designed for single engineer or small team (< 10)
- Memory bank up to ~10,000 documents before performance tuning needed
- FAISS flat index sufficient for MVP; IVF index for larger scale
- SQLite handles millions of rows without issue at this scale

## Current Status

Architecture defined. Implementation not started.
Last updated: 2026-05-15
