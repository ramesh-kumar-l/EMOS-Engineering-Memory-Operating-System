# EMOS — Getting Started Guide

Everything a new engineer needs to understand, install, and use EMOS from zero.

---

## Table of Contents

1. [What Is EMOS?](#1-what-is-emos)
2. [What Problem Does It Solve?](#2-what-problem-does-it-solve)
3. [How Does It Work? (Architecture Overview)](#3-how-does-it-work)
4. [Prerequisites](#4-prerequisites)
5. [Installation](#5-installation)
6. [Running EMOS](#6-running-emos)
7. [Feature Walkthrough](#7-feature-walkthrough)
   - [Dashboard](#71-dashboard)
   - [Memory Bank](#72-memory-bank)
   - [Semantic Search](#73-semantic-search)
   - [Context Assembly](#74-context-assembly)
   - [Prompt Registry](#75-prompt-registry)
   - [Workflow Engine](#76-workflow-engine)
   - [Repo Intelligence](#77-repo-intelligence)
   - [Memory Graph](#78-memory-graph)
8. [Your First 10 Minutes with EMOS](#8-your-first-10-minutes)
9. [Frequently Asked Questions](#9-faq)
10. [Troubleshooting](#10-troubleshooting)
11. [Project Structure](#11-project-structure)
12. [Configuration Reference](#12-configuration-reference)

---

## 1. What Is EMOS?

EMOS (Engineering Memory Operating System) is a **local, offline-first engineering intelligence layer** that lives alongside your development workflow.

Think of it as your engineering brain's external hard drive:
- It remembers architectural decisions you made months ago
- It remembers why a dependency was chosen and what was rejected
- It stores your best prompt templates and tracks which ones worked
- It guides you through deterministic engineering workflows
- It analyzes your codebase structure and flags coupling risks
- It assembles perfectly-sized context packages for your AI sessions

**What EMOS is NOT:**
- It is not an autonomous agent that writes code for you
- It is not an IDE replacement
- It is not a chatbot wrapper
- It is not a cloud platform

**The golden rule:** AI assists. You decide. Every step.

---

## 2. What Problem Does It Solve?

Every engineer working with AI tools hits the same wall:

**AI sessions are stateless.** Every new conversation starts cold. The AI knows nothing about your project, your constraints, your past decisions, or why your codebase looks the way it does. You spend 20 minutes re-explaining context. Then the AI hallucinates a library that doesn't exist, or suggests an architecture you already rejected three months ago.

EMOS fixes this by:

1. **Persisting engineering memory** — Your decisions, architecture, constraints, and lessons live in a structured Markdown-based memory bank that survives indefinitely.
2. **Semantic retrieval** — When you start an AI session, EMOS finds the most relevant memories and assembles them into a token-efficient context package automatically.
3. **Reliable prompting** — A versioned prompt template library with usage tracking so you know which prompts consistently produce good results.
4. **Deterministic workflows** — Step-by-step engineering workflows (architecture review, debugging, documentation) with human confirmation at each gate.
5. **Repo intelligence** — Tree-sitter-powered structural analysis that understands your codebase without you having to explain it.

---

## 3. How Does It Work?

```
Your Engineering Work
        │
        ▼
  Memory Bank (Markdown + SQLite)
        │
        ▼
  Semantic Retrieval (FAISS + FTS5)
        │
        ▼
  Context Assembly (token-budget packing)
        │
        ▼
  Claude API (optional — offline-first by default)
        │
        ▼
  Reliability Validation → You decide what to keep
```

**Storage design:**
| What | Where | Why |
|------|-------|-----|
| Memory documents | Markdown files | Human-readable, git-trackable, no tooling needed |
| Fast lookup index | SQLite + FTS5 | Zero-server, sub-100ms keyword search |
| Vector embeddings | FAISS flat index | Local, no cloud, fast similarity search |
| Prompt templates | SQLite | Versioned, queryable |
| Workflow state | SQLite | Durable across sessions |

**Two servers, one UI:**
- Backend: Python/FastAPI on `localhost:8000` — all the intelligence
- Frontend: Next.js on `localhost:3000` — the UI you interact with

---

## 4. Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| Python | 3.11+ | 3.14 confirmed working on Windows 11 |
| Node.js | 18+ | 20 LTS recommended |
| npm | 9+ | Comes with Node |
| Git | Any | For cloning |
| Claude API key | Optional | Required only for AI context assembly |

**Platform support:**
- Windows 11 ✅ (primary development platform)
- Linux ✅ (pathlib used throughout — no hardcoded separators)
- macOS ✅ (untested but should work)

**Disk space:** ~2GB for Python ML dependencies (PyTorch + sentence-transformers). The AI model (`all-MiniLM-L6-v2`, ~80MB) downloads on first semantic search use and is cached locally.

---

## 5. Installation

### 5.1 Clone the Repository

```bash
git clone <your-repo-url> EMOS
cd EMOS
```

### 5.2 Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install core dependencies
pip install -e .

# Install ML dependencies (needed for semantic search)
pip install -e ".[ml]"

# Install repo intelligence dependencies (needed for code analysis)
pip install -e ".[intel]"

# Run database migrations
alembic upgrade head
```

### 5.3 Configure Environment

Create a `.env` file in the `backend/` directory:

```env
# Required for AI context assembly (optional feature)
ANTHROPIC_API_KEY=sk-ant-...

# Storage paths (defaults work out of the box)
MEMORY_BANK_PATH=../memory-bank
SQLITE_PATH=../data/emos.db
FAISS_INDEX_PATH=../data/indexes
```

If you don't have a Claude API key, leave `ANTHROPIC_API_KEY` unset. All features except AI context assembly will still work.

### 5.4 Frontend Setup

```bash
cd frontend
npm install
```

No additional configuration needed — the frontend connects to `localhost:8000` by default.

### 5.5 Verify Backend Tests (Optional but Recommended)

```bash
cd backend
pytest
# Expected: 128/128 tests passing
```

---

## 6. Running EMOS

Open two terminals:

**Terminal 1 — Backend:**
```bash
cd backend
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
uvicorn backend.main:app --reload
# Listening on http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Listening on http://localhost:3000
```

Open your browser to `http://localhost:3000`.

**Backend API docs** are available at `http://localhost:8000/docs` (auto-generated OpenAPI/Swagger UI). This is useful for exploring endpoints directly.

---

## 7. Feature Walkthrough

### 7.1 Dashboard

**URL:** `localhost:3000/`

The dashboard gives you a live status overview:
- **Memory Documents** — total documents in your memory bank
- **Vector Index** — whether the semantic search index has been built and how many documents are indexed
- **Active Workflows** — workflow runs currently in progress

It also provides quick-access cards to every major feature.

If you see `—` instead of numbers, the backend isn't running. Check Terminal 1.

---

### 7.2 Memory Bank

**URL:** `localhost:3000/memory`

The memory bank is the heart of EMOS. It's a collection of structured Markdown documents organized by category.

**What to store here:**
- Architectural decisions (why you chose FastAPI over Express, why you rejected PostgreSQL)
- System constraints (token budget limits, offline-first requirement)
- Engineering lessons (what failed in production and why)
- Technical debt (shortcuts taken and their resolution path)
- Roadmap (what's done, what's next)
- Glossary (project-specific terms)

**How to use the Memory Bank page:**
1. **Browse** — All documents appear as cards with category, tags, and a content preview
2. **Search** — Type in the search box to run full-text keyword search (SQLite FTS5)
3. **Filter by category** — Use the category dropdown to narrow results
4. **Sync from disk** — Click "Sync" to import Markdown files from the `memory-bank/` directory into the database
5. **Create** — Click "New Document" to write a new memory
6. **Edit/Delete** — Click any document to open it, then use the Edit or Delete buttons

**Document format:**
Every document has:
- `slug` — unique identifier (lowercase, hyphenated, e.g., `architecture-decisions`)
- `title` — human-readable name
- `category` — one of: architecture, decisions, constraints, lessons, roadmap, etc.
- `tags` — array of strings (used to draw edges in the memory graph)
- `content` — Markdown body

**The Sync button** is important: if you edit Markdown files directly in `memory-bank/` (e.g., via VS Code), click Sync to bring those changes into the database.

---

### 7.3 Semantic Search

**URL:** `localhost:3000/search`

Three search modes:

| Mode | How It Works | Best For |
|------|-------------|---------|
| **Keyword** | SQLite FTS5 full-text search with Porter stemming | Exact terms, known words |
| **Semantic** | FAISS cosine similarity over sentence-transformer embeddings | Meaning-based search, paraphrased queries |
| **Hybrid** | Weighted fusion of FTS5 + FAISS scores | Best results for most queries |

**Before you can use Semantic or Hybrid mode**, you need to build the vector index:
1. Click **"Build Index"** button on the search page
2. Wait for the index to build (seconds for small memory banks, minutes for thousands of documents)
3. The index status in the top-right shows "ready" when done

The alpha slider (0–1) controls the blend ratio in Hybrid mode:
- `alpha = 0.0` → pure keyword
- `alpha = 1.0` → pure semantic
- `alpha = 0.5` → equal blend (default)

**Example queries that work well with semantic search:**
- "why did we choose this database" (finds decisions about database selection even if those words aren't in the document)
- "offline constraint" (finds documents about local-only requirements)
- "what failed in production" (finds lessons and incidents)

---

### 7.4 Context Assembly

**URL:** `localhost:3000/context`

This feature assembles an optimized context package for an AI session.

**How it works:**
1. You enter a query describing what you're working on (e.g., "implementing the new auth middleware")
2. EMOS runs hybrid search across your memory bank
3. Retrieved chunks are ranked by relevance + recency (30-day half-life decay)
4. Chunks are greedily packed into your token budget
5. The assembled context is displayed and can be copied to clipboard

**Controls:**
- **Query** — what you're working on right now
- **Token Budget** — how many tokens to allocate (1K–200K). Default 80K leaves room for AI response.
- **Alpha** — semantic vs. keyword blend (same as search page)
- **Recency Weight** — how much to boost recent documents vs. purely relevant ones

**Output:** A formatted Markdown block containing the most relevant engineering memory for your current task. Paste this at the start of your Claude/ChatGPT conversation.

**Note:** If you have `ANTHROPIC_API_KEY` set in your `.env`, EMOS can also send this context directly to Claude and show you the response. Without the key, you just get the assembled context text to paste manually.

---

### 7.5 Prompt Registry

**URL:** `localhost:3000/prompts`

A versioned library of your most useful AI prompts.

**Why this matters:** Good prompts are engineering assets. They should be versioned, reusable, and tracked like code.

**Features:**
- **Create templates** with `{parameter}` placeholders (EMOS auto-detects parameters)
- **Render** — fill in parameters and preview the final prompt before using it
- **Version history** — every edit increments the version number automatically
- **Usage tracking** — log what parameters you used, the outcome, and token counts
- **Category filtering** — organize by category (debugging, architecture, review, etc.)

**Example template:**
```
Review the following {language} function for {concern}:

{code}

Focus specifically on: correctness, edge cases, and {secondary_concern}.
```

Parameters detected: `language`, `concern`, `code`, `secondary_concern`

**How to use the Render feature:**
1. Open any template
2. Click "Render"
3. Fill in the parameter inputs
4. Copy the rendered prompt

---

### 7.6 Workflow Engine

**URL:** `localhost:3000/workflows`

Six built-in engineering workflow templates, each with step-by-step human-gated execution:

| Workflow | Purpose |
|----------|---------|
| Architecture Review | Validate a new design before implementation |
| Implementation | Feature build with memory-grounded context |
| Debugging | Diagnose failures with context continuity |
| Evaluation | Assess reliability and correctness |
| Documentation | Generate and maintain engineering docs |
| Release Preparation | Audit and prepare a reliable release |

**Golden rule: no step executes autonomously.** Every step requires your confirmation before the workflow advances.

**Starting a workflow:**
1. Click any workflow definition card
2. Click "Start Run"
3. Optionally add context (what this run is about)
4. The run opens in step-detail view

**Advancing a step:**
1. Read the current step description
2. Do the work described (EMOS guides you; it doesn't do it for you)
3. Record the outcome (what happened, your notes)
4. Click "Advance" to move to the next step

**Run states:** Each step is either `pending`, `current`, or `done`. The overall run is `running`, `completed`, or `cancelled`.

**Cancelling:** Click "Cancel Run" to abort a workflow at any step. The state is preserved in the database.

---

### 7.7 Repo Intelligence

**URL:** `localhost:3000/repo`

Analyze any directory on your machine using Tree-sitter AST parsing.

**Three tabs:**

**Analyze tab:**
- Enter a local directory path (e.g., `E:\MyProject\src`)
- EMOS walks the directory, parses Python/JS/TS/JSX/TSX files
- Returns: file count, symbol count, language breakdown, per-file summary (function count, class count, imports)
- Useful for understanding a new codebase quickly

**Risks tab:**
- Enter a directory path
- Detects three coupling risk types:
  - **High fan-out** (≥10 imports from one file) — that file depends on too much
  - **High fan-in** (≥8 files importing from one file) — that file is a critical bottleneck
  - **Circular dependency** — A imports B imports A (deadlock risk)
- Each risk shows a severity badge (low/medium/high)

**Docs tab:**
- Enter a directory path and optional title
- EMOS generates a full Markdown documentation document:
  - Overview table (file counts, symbol counts by language)
  - Language breakdown
  - File index with extracted symbols
- Click "Copy Markdown" and paste into your memory bank or documentation

**Important:** Repo intelligence is stateless — analysis runs on demand and results are not persisted. Run it again whenever you want fresh data.

---

### 7.8 Memory Graph

**URL:** `localhost:3000/graph`

An interactive React Flow visualization of your memory bank.

- Each **node** is a memory document
- **Edges** connect documents that share tags
- Documents are arranged in **category rings** — each category gets its own orbital cluster
- Click any node to open the inspector panel (title, category, tags, content preview, link to full document)

**How to use it:**
- Use the mouse wheel to zoom in/out
- Drag to pan
- Click a node to inspect it
- Use the MiniMap (bottom-right) for navigation on large memory banks
- The Controls (bottom-left) offer fit-to-view, zoom in/out

**What to look for:**
- Isolated nodes (no edges) have unique tags — they may be orphaned memories
- Highly connected nodes are central concepts — they're your most cross-referenced memories
- Dense clusters indicate a tightly coupled knowledge area

---

## 8. Your First 10 Minutes

Follow this sequence to go from zero to productive:

**Minutes 1–2: Start everything**
```bash
# Terminal 1
cd backend && .venv\Scripts\activate && uvicorn backend.main:app --reload

# Terminal 2
cd frontend && npm run dev
```
Open `localhost:3000`. You should see the dashboard.

**Minutes 3–4: Sync the memory bank**
1. Go to Memory Bank (`/memory`)
2. Click **"Sync"** — this loads the pre-existing `memory-bank/` Markdown files into SQLite
3. You should see cards for vision, architecture, roadmap, decisions, constraints, and more

**Minutes 5–6: Build the vector index**
1. Go to Search (`/search`)
2. Click **"Build Index"**
3. Wait for "ready" status
4. Try a semantic search: type "why offline first" and see what comes back

**Minutes 7–8: Assemble your first context**
1. Go to Context (`/context`)
2. Type a query like "offline storage decisions"
3. Set budget to 40,000 tokens
4. Click **"Assemble Context"**
5. Copy the result — this is what you'd paste into an AI session

**Minutes 9–10: Explore a workflow**
1. Go to Workflows (`/workflows`)
2. Click the "Architecture Review" definition
3. Start a run (no context needed for a test)
4. Explore the step interface — note that nothing advances without your click

---

## 9. FAQ

**Q: Do I need a Claude API key?**
A: No. All features work offline except the "Send to Claude" button in Context Assembly. The key is optional.

**Q: Where is my data stored?**
A: Everything is local:
- Markdown files: `memory-bank/`
- SQLite database: `data/emos.db`
- FAISS vector index: `data/indexes/memory.faiss` + `data/indexes/memory_meta.json`

**Q: Can I use EMOS with non-Python repos?**
A: Yes. The memory bank works with any codebase. Repo Intelligence supports Python, JavaScript, TypeScript, JSX, and TSX via Tree-sitter. More languages can be added by installing additional Tree-sitter grammars.

**Q: What happens if I edit a memory document in VS Code directly?**
A: Edit the Markdown file, then click "Sync" in the Memory Bank UI. The change will be imported into SQLite and re-indexed.

**Q: Is semantic search accurate without fine-tuning?**
A: Reasonably so. The model (`all-MiniLM-L6-v2`) is a general-purpose sentence embedding model. For engineering-domain content it performs well on concept-level retrieval. Hybrid mode (alpha=0.5) usually outperforms pure semantic or pure keyword alone.

**Q: How big can the memory bank get?**
A: The system is designed for up to 10,000 documents before needing tuning. At that scale:
- SQLite FTS5 keyword search: <100ms
- FAISS flat index semantic search: <500ms
- Context assembly: <2s

For larger scales, FAISS can be upgraded from flat (IndexFlatIP) to IVF index without changing the API.

**Q: Can multiple engineers share a memory bank?**
A: Not in the current MVP. Multi-user collaboration is a deferred post-MVP feature. The simplest workaround today is to commit the `memory-bank/` Markdown files to a shared git repository.

**Q: How do I back up my data?**
A: Commit `memory-bank/` to git — that's your canonical backup. The SQLite database (`data/emos.db`) is a derived cache that can always be regenerated by running Sync. The FAISS index is also regenerated by clicking "Build Index".

**Q: How do I add my own workflow?**
A: Workflows are currently hardcoded as Python dataclasses in the backend. To add a custom workflow, add a new entry to the workflow definitions file in `backend/` and restart the backend server. A user-defined workflow editor is a post-MVP feature.

**Q: Why FastAPI instead of Node/Express?**
A: Python is required for sentence-transformers and FAISS — those libraries don't have production-equivalent Node equivalents. Using Python for the backend allows native integration with the ML stack without a polyglot bridge.

**Q: What is the "reliability layer" mentioned in the architecture docs?**
A: The reliability layer validates AI outputs against known facts in the memory bank, flags hallucination risks, and assigns confidence scores to retrieval results. It's designed to surface when AI suggestions conflict with documented constraints or decisions. It's wired into the backend and exposed via confidence scores in search results.

---

## 10. Troubleshooting

### "Cannot connect to backend" / Dashboard shows `—`

The backend isn't running or crashed. Check Terminal 1:
```bash
uvicorn backend.main:app --reload
```
Common causes:
- Virtual environment not activated
- Missing `.env` file
- Port 8000 already in use — kill the other process or change the port

### "Index not ready" on Search page

The FAISS vector index hasn't been built yet. Click "Build Index" on the Search page.

### Semantic search returns no results

Check: is the index ready? Is the query non-empty? Try switching to Keyword mode first to verify documents exist in the database.

### `ModuleNotFoundError: No module named 'sentence_transformers'`

You need the ML extras:
```bash
pip install -e ".[ml]"
```

### `ModuleNotFoundError: No module named 'tree_sitter'`

You need the repo intelligence extras:
```bash
pip install -e ".[intel]"
```

### First semantic search takes 30–60 seconds

The embedding model (`all-MiniLM-L6-v2`) is downloading on first use (~80MB). Subsequent loads use the local cache and are instant.

### Alembic migration error on startup

```bash
alembic upgrade head
```
Run this from the `backend/` directory with the virtual environment active.

### CORS errors in the browser console

The backend must be running at `localhost:8000`. CORS is pre-configured to allow `localhost:3000`. If you changed the port on either side, update the CORS settings in `backend/main.py` and the `BASE` URL in `frontend/lib/api.ts`.

---

## 11. Project Structure

```
EMOS/
├── memory-bank/              # Source-of-truth engineering memory (Markdown)
│   ├── vision.md             # Product philosophy and goals
│   ├── architecture.md       # System design and component boundaries
│   ├── roadmap.md            # Implementation phases and status
│   ├── decisions.md          # Architectural Decision Records (ADRs)
│   ├── constraints.md        # Hard technical and scope constraints
│   ├── workflows.md          # Engineering workflow definitions
│   ├── lessons.md            # Engineering lessons log
│   ├── technical-debt.md     # Tracked shortcuts and resolution paths
│   ├── dependencies.md       # Package versions and risk assessment
│   ├── evaluations.md        # System reliability assessments
│   ├── reliability-status.md # Current reliability health
│   ├── glossary.md           # Project-specific terminology
│   ├── prompts-used.md       # Prompts log
│   ├── changelog.md          # Release history
│   └── risks.md              # Risk register
│
├── backend/                  # FastAPI Python backend
│   ├── api/                  # Route handlers (memory, retrieval, context, etc.)
│   ├── core/                 # Shared config, base models, dependency injection
│   ├── memory/               # Memory bank engine (Markdown CRUD + SQLite)
│   ├── retrieval/            # FAISS + FTS5 hybrid search
│   ├── context/              # Token-budget context assembly + Claude API
│   ├── prompts/              # Prompt template CRUD + usage tracking
│   ├── workflows/            # Workflow definitions + execution engine
│   ├── repo_intel/           # Tree-sitter AST analysis
│   ├── tests/                # 128 tests (pytest)
│   ├── alembic/              # Database migration scripts
│   ├── pyproject.toml        # Dependencies and project config
│   └── main.py               # FastAPI app entry point
│
├── frontend/                 # Next.js 16 + React + Tailwind UI
│   ├── app/                  # App Router pages
│   │   ├── page.tsx          # Dashboard
│   │   ├── memory/           # Memory Bank browser + document CRUD
│   │   ├── search/           # Semantic + keyword search
│   │   ├── context/          # Context assembly
│   │   ├── prompts/          # Prompt registry
│   │   ├── workflows/        # Workflow runner
│   │   ├── repo/             # Repo intelligence
│   │   └── graph/            # Memory relationship graph
│   ├── components/           # Shared UI components (NavSidebar, etc.)
│   ├── lib/                  # API client (api.ts), types (types.ts), utils
│   └── package.json
│
└── data/                     # Runtime data (auto-created, not committed)
    ├── emos.db               # SQLite database
    └── indexes/              # FAISS vector index files
```

---

## 12. Configuration Reference

### Backend `.env` Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `ANTHROPIC_API_KEY` | (unset) | No | Claude API key for AI context assembly |
| `MEMORY_BANK_PATH` | `../memory-bank` | No | Path to Markdown memory documents |
| `SQLITE_PATH` | `../data/emos.db` | No | SQLite database file path |
| `FAISS_INDEX_PATH` | `../data/indexes` | No | Directory for FAISS index files |

### Frontend Environment

No configuration needed by default. If your backend runs on a different port, edit `frontend/lib/api.ts`:

```typescript
const BASE = "http://localhost:8000/api/v1";  // change port here
```

### Performance Tuning

For memory banks larger than 5,000 documents:
- Switch FAISS from `IndexFlatIP` to `IndexIVFFlat` in `backend/retrieval/engine.py`
- Increase SQLite cache size: `PRAGMA cache_size = -64000` (64MB)

---

*Built with FastAPI · SQLite · FAISS · sentence-transformers · Tree-sitter · Next.js 16 · React Flow*
