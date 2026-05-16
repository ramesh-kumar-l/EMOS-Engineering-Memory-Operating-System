# Dependencies

## Backend (Python)

| Package               | Version (target) | Purpose                        | Risk                          |
|-----------------------|------------------|--------------------------------|-------------------------------|
| fastapi               | ^0.111           | API framework                  | Low                           |
| uvicorn               | ^0.29            | ASGI server                    | Low                           |
| pydantic              | ^2.7             | Data validation                | Low                           |
| sqlalchemy            | ^2.0             | SQLite ORM                     | Low                           |
| alembic               | ^1.13            | DB migrations                  | Low                           |
| sentence-transformers | ^3.0             | Local embeddings               | Medium — large PyTorch dep    |
| faiss-cpu             | ^1.8             | Vector similarity search       | Medium — Windows native build |
| tree-sitter           | ^0.22            | Code parsing                   | Low                           |
| anthropic             | ^0.28            | Claude API client              | Low                           |
| python-dotenv         | ^1.0             | Env config                     | Low                           |
| pytest                | ^8.0             | Testing                        | Low                           |

## Frontend (Node)

| Package          | Version (target) | Purpose                  | Risk |
|------------------|------------------|--------------------------|------|
| next             | ^14              | React framework          | Low  |
| react            | ^18              | UI library               | Low  |
| tailwindcss      | ^3               | Styling                  | Low  |
| reactflow        | ^11              | Graph visualization      | Low  |
| typescript       | ^5               | Type safety              | Low  |

## Environment Requirements

- Python: 3.11+
- Node.js: 18+
- OS: Windows 11 (primary), Linux/macOS (target portability)

## Actual Installed Versions (Python 3.14.4, Windows 11)

| Package           | Installed | Notes                                      |
|-------------------|-----------|--------------------------------------------|
| fastapi           | 0.136.1   | Confirmed working                          |
| uvicorn           | 0.47.0    | Confirmed working                          |
| pydantic          | 2.13.4    | 2.10.x had no 3.14 wheel; 2.11+ required  |
| pydantic-settings | 2.14.1    | Confirmed working                          |
| sqlalchemy        | 2.0.49    | Confirmed working                          |
| alembic           | 1.18.4    | Confirmed working                          |
| pyyaml            | 6.0.3     | Confirmed working                          |
| pytest            | 8.3.4     | 21/21 tests passing                        |
| httpx             | 0.28.1    | Confirmed working                          |

## ML Dependencies (Phase 2 — Validated ✅)

| Package              | Installed | Notes                                         |
|----------------------|-----------|-----------------------------------------------|
| faiss-cpu            | 1.13.2    | Python 3.14 wheel available — no sub-venv     |
| sentence-transformers| 5.5.0     | Python 3.14 wheel available — no sub-venv     |
| torch                | 2.12.0    | Pulled in by sentence-transformers            |
| numpy                | 2.4.4     | Pulled in by faiss-cpu                        |

Both packages install cleanly on Python 3.14.4 / Windows 11.
Model used: all-MiniLM-L6-v2 (80MB, downloads on first use, then cached locally).
