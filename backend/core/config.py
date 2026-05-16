from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EMOS"
    app_version: str = "0.1.0"
    debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    token_budget: int = 80_000

    # Optional — needed only for Phase 3 Claude integration
    anthropic_api_key: str | None = None

    # Resolved at runtime — not read from env
    _project_root: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def memory_bank_dir(self) -> Path:
        return self._project_root / "memory-bank"

    @property
    def data_dir(self) -> Path:
        return self._project_root / "data"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'emos.db'}"

    @property
    def faiss_index_dir(self) -> Path:
        return self.data_dir / "indexes"


@lru_cache
def get_settings() -> Settings:
    return Settings()
