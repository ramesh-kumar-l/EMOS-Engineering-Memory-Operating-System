# Architectural Decisions

## ADR-001: Markdown as Primary Memory Storage
**Date:** 2026-05-15
**Status:** Accepted

**Decision:** All memory bank documents are stored as Markdown files. SQLite serves as a query cache and index, not the source of truth.

**Rationale:**
- Markdown is human-readable without any tooling
- Git-trackable natively
- AI-readable without transformation
- Zero dependency for reading/writing
- Survives tool changes

**Rejected Alternative:** Pure database storage (SQLite/PostgreSQL)
**Reason for rejection:** Locks memory into a binary format, loses human readability, requires tooling to inspect.

---

## ADR-002: FAISS for Local Vector Storage
**Date:** 2026-05-15
**Status:** Accepted

**Decision:** Use FAISS (flat index for MVP) for semantic vector storage and retrieval.

**Rationale:**
- Fully local, no cloud dependency
- Fast similarity search
- Well-maintained, production-proven
- Python-native integration

**Rejected Alternative:** ChromaDB, Pinecone
**Reason for rejection:** ChromaDB adds server complexity; Pinecone is cloud-only. Both conflict with offline-first requirement.

---

## ADR-003: FastAPI for Backend
**Date:** 2026-05-15
**Status:** Accepted

**Decision:** Python FastAPI as the backend framework.

**Rationale:**
- Native Python ecosystem for ML/AI libraries (sentence-transformers, FAISS, Tree-sitter)
- Async support
- Auto-generated OpenAPI docs
- Lightweight, minimal overhead

**Rejected Alternative:** Node.js/Express
**Reason for rejection:** Python is mandatory for sentence-transformers and FAISS; mixing languages adds unnecessary complexity at MVP stage.

---

## ADR-004: Human-Gated Workflow Execution
**Date:** 2026-05-15
**Status:** Accepted

**Decision:** No workflow step executes autonomously. Every step requires human confirmation before proceeding.

**Rationale:**
- Core principle: AI assists, humans govern
- Prevents irreversible automated actions
- Preserves trust and auditability

**Rejected Alternative:** Autonomous multi-step execution
**Reason for rejection:** Violates human governance principle. Out of MVP scope.

---

## ADR-005: Local-Only API by Default
**Date:** 2026-05-15
**Status:** Accepted

**Decision:** All FastAPI endpoints bind to localhost only. No external network exposure by default.

**Rationale:**
- Privacy-preserving
- Offline-first
- Reduces attack surface
- Cloud access is opt-in enhancement only
