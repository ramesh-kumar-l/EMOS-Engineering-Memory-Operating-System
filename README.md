# EMOS — Engineering Memory Operating System

An offline-first engineering memory and workflow operating system.

## What It Is

EMOS is an engineering cognition layer that preserves engineering intelligence across sessions, repos, and team changes. It enables reliable AI-assisted development with persistent memory, semantic retrieval, and deterministic workflows.

## What It Is Not

- Not an autonomous coding agent
- Not an IDE replacement
- Not a cloud-first platform
- Not a chatbot wrapper

## Core Principles

1. Offline-first — works without internet
2. Reliability-first — explicit hallucination guards
3. Human-governed — AI assists, humans decide
4. Privacy-preserving — all data local by default

## Architecture

```
EMOS/
├── memory-bank/     # Engineering memory (Markdown + SQLite)
├── backend/         # FastAPI Python backend
├── frontend/        # Next.js + React + Tailwind
└── data/            # Local SQLite + FAISS indexes
```

## Status

Pre-implementation. Memory bank scaffolded. Architecture defined.

See `memory-bank/roadmap.md` for implementation phases.

## Tech Stack

- Backend: Python, FastAPI, SQLite, FAISS, sentence-transformers, Tree-sitter
- Frontend: Next.js, React, Tailwind, React Flow
- AI: Claude API (optional — offline-first by design)
