# Risks

## Active Risks

### RISK-001: FAISS + sentence-transformers Windows Installation
**Severity:** High
**Probability:** Medium
**Status:** Unvalidated

FAISS and sentence-transformers have native dependencies that can fail on Windows, especially with certain Python versions or virtual environment configurations. sentence-transformers pulls in PyTorch, which is a large dependency with occasional Windows compatibility issues.

**Mitigation:** Validate environment in Phase 0 before any implementation begins. Document exact working versions in dependencies.md.

---

### RISK-002: Token Budget Overflow in Context Assembly
**Severity:** Medium
**Probability:** Medium
**Status:** Mitigated by design

As the memory bank grows, context assembly could exceed Claude API token limits, degrading response quality or causing errors.

**Mitigation:** Token budget is enforced at context loader level. Chunks are ranked and truncated before assembly. Default budget is 80K tokens with headroom for response.

---

### RISK-003: SQLite Index Drift from Markdown Source
**Severity:** Medium
**Probability:** Low
**Status:** Mitigated by design

If Markdown files are edited outside of EMOS tooling, the SQLite index can become stale.

**Mitigation:** Index rebuild command available. Index is always treated as cache, not source of truth. Markdown files are authoritative.

---

### RISK-004: Scope Creep Beyond MVP Boundary
**Severity:** High
**Probability:** Medium
**Status:** Active — governance required

The MVP boundary is intentionally narrow. Pressure to add autonomous agents, cloud sync, or IDE integration before P0 is complete is a real risk.

**Mitigation:** MVP boundary is documented and enforced. Any scope addition requires explicit ADR entry with rationale.

---

### RISK-005: Tree-sitter Language Support Gaps
**Severity:** Low
**Probability:** Low
**Status:** Acceptable

Tree-sitter may not have parsers for all languages in a given repo. Repo intelligence will silently skip unsupported file types.

**Mitigation:** Explicitly document supported languages. Gracefully handle unsupported files. No hallucinated analysis for unknown file types.

---

### RISK-006: Claude API Rate Limits or Unavailability
**Severity:** Low (by design)
**Probability:** Medium
**Status:** Mitigated by design

Claude API calls are optional. All core EMOS features work without them.

**Mitigation:** Offline-first architecture ensures no hard dependency on Claude API at MVP.
