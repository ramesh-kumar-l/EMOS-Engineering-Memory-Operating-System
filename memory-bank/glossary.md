# Glossary

## EMOS Terms

**EMOS** — Engineering Memory Operating System. The full product.

**Memory Bank** — The structured collection of Markdown documents that constitute EMOS's persistent engineering intelligence.

**Semantic Retrieval** — Finding relevant memory chunks using vector similarity search (FAISS) in addition to keyword search.

**Context Assembly** — The process of selecting and packaging memory chunks into a token-efficient prompt for Claude.

**Reliability Layer** — The component responsible for validating AI outputs, flagging hallucination risks, and assigning confidence scores.

**Repo Intelligence** — Lightweight static analysis of a code repository using Tree-sitter to understand structure, patterns, and risks.

**Prompt Registry** — A versioned collection of reusable prompt templates stored as Markdown.

**Workflow Engine** — The system that defines and executes deterministic, human-gated engineering workflows.

**Human Governance** — The principle that all consequential decisions require human review and approval; AI assists, humans decide.

**Offline-First** — Architecture where all core features work without internet connectivity.

**ADR** — Architectural Decision Record. A documented decision with rationale and rejected alternatives.

**FTS5** — SQLite's full-text search extension, used for fast keyword search over the memory bank.

**FAISS** — Facebook AI Similarity Search. A library for efficient similarity search over dense vectors.

**sentence-transformers** — A Python library for generating sentence-level embeddings locally.

**Tree-sitter** — A parser generator and incremental parsing library used for code structure analysis.

**Token Budget** — The maximum number of tokens allocated for context assembly before sending to Claude API.

**Confidence Score** — A numerical estimate of how reliable a retrieved chunk or AI output is.

**Hybrid Search** — Combining keyword search (FTS5) and semantic search (FAISS) to improve retrieval precision.
