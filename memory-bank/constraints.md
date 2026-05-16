# Constraints

## Technical Constraints

### Offline-First (Hard Constraint)
- All critical workflows must operate without internet connectivity
- Claude API calls are optional enhancement; core features must not depend on them
- No required cloud services at MVP

### Local Storage Only (Hard Constraint)
- All data stays on the local machine by default
- No external databases, no cloud sync in MVP
- FAISS indexes are local files; SQLite database is a local file

### Windows Compatibility (Current Environment)
- Primary development environment: Windows 11
- Python dependencies must be installable on Windows
- Path handling must be cross-platform (use pathlib, not hardcoded separators)
- FAISS: use faiss-cpu (faiss-gpu not required for MVP)

### Python Version
- Target: Python 3.11+
- sentence-transformers requires compatible numpy/torch versions
- Validate environment compatibility early

### Token Budget
- Claude API context window: respect limits in context loader
- Default budget: 80,000 tokens per context assembly (leaves headroom for response)
- Memory chunks must be summarizable to fit budget constraints

## Scope Constraints

### MVP Boundary (Hard Constraint)
Only P0 features are in scope. Any feature not in the approved list requires explicit decision to add, with rationale documented in decisions.md.

### No Autonomous Execution
- No code is executed autonomously by the AI layer
- No files are modified without human confirmation
- No network requests are made on behalf of users without explicit action

## Performance Constraints

### Retrieval Latency
- Semantic search target: < 500ms for up to 10,000 documents
- Keyword search target: < 100ms (SQLite FTS5)
- Context assembly target: < 2s total

### Memory Bank Size
- MVP target: up to 10,000 Markdown documents
- FAISS flat index is sufficient at this scale
- SQLite handles this without tuning

## Security Constraints

### API Security
- Localhost binding only by default
- No authentication required for local-only mode (single-user assumption)
- API keys for Claude stored in local .env file, never committed

### Data Privacy
- No telemetry
- No analytics
- No external network calls except Claude API (opt-in)
