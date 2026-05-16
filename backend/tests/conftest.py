from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..api.v1.memory import get_mem_engine
from ..core.base import Base
from ..core.database import get_db
from ..main import app
from ..memory import models as _memory_models  # noqa: F401 — registers MemoryDocument with Base
from ..memory.engine import MemoryBankEngine
from ..memory.service import MemoryService
from ..prompts import models as _prompt_models  # noqa: F401 — registers PromptTemplate, PromptUsage
from ..workflows import models as _workflow_models  # noqa: F401 — registers WorkflowRun, WorkflowStepRecord


@pytest.fixture(scope="function")
def tmp_db(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    with eng.connect() as conn:
        conn.execute(text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts "
            "USING fts5(slug UNINDEXED, title, content, tokenize='porter ascii')"
        ))
        conn.commit()
    return eng


@pytest.fixture(scope="function")
def db_session(tmp_db) -> Session:
    Factory = sessionmaker(bind=tmp_db)
    session = Factory()
    yield session
    session.close()


@pytest.fixture(scope="function")
def mem_engine(tmp_path: Path) -> MemoryBankEngine:
    return MemoryBankEngine(base_dir=tmp_path / "memory-bank")


@pytest.fixture(scope="function")
def service(db_session: Session, mem_engine: MemoryBankEngine) -> MemoryService:
    return MemoryService(db=db_session, engine=mem_engine)


@pytest.fixture(scope="function")
def client(tmp_db, mem_engine: MemoryBankEngine) -> TestClient:
    Factory = sessionmaker(bind=tmp_db)

    def _override_db():
        session = Factory()
        try:
            yield session
        finally:
            session.close()

    def _override_engine() -> MemoryBankEngine:
        return mem_engine

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_mem_engine] = _override_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
