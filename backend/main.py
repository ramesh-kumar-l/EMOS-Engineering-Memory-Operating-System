import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .api.router import api_router
from .core.config import get_settings
from .core.database import engine
from .core.exceptions import EMOSError, to_http
from .memory.models import Base

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger("emos")


def _bootstrap_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.faiss_index_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # FTS5 virtual tables are not created by SQLAlchemy metadata — must use raw SQL.
        conn.execute(text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts "
            "USING fts5(slug UNINDEXED, title, content, tokenize='porter ascii')"
        ))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    _bootstrap_db()
    logger.info("EMOS started. Memory bank: %s | DB: %s", settings.memory_bank_dir, settings.database_url)
    yield
    logger.info("EMOS shutting down.")


app = FastAPI(
    title="EMOS API",
    version=settings.app_version,
    description="Engineering Memory Operating System — offline-first local REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Localhost-only origins — no external domains permitted by design (ADR-005)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EMOSError)
async def _emos_error_handler(request: Request, exc: EMOSError) -> JSONResponse:
    http_exc = to_http(exc)
    return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})


app.include_router(api_router, prefix="/api/v1")
