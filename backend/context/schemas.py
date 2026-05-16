from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ContextChunk(BaseModel):
    slug: str
    title: str
    category: str | None = None
    content: str
    relevance_score: float
    recency_score: float
    final_score: float
    token_count: int


class ContextPackage(BaseModel):
    query: str
    chunks: list[ContextChunk]
    total_tokens: int
    token_budget: int
    budget_used_pct: float
    assembled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: Literal["hybrid", "semantic", "keyword"] = "hybrid"
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    token_budget: int = Field(80_000, ge=1_000, le=200_000)
    max_chunks: int = Field(20, ge=1, le=100)
    recency_weight: float = Field(0.3, ge=0.0, le=1.0)
    send_to_claude: bool = False
    claude_prompt: str | None = None


class ContextResponse(BaseModel):
    package: ContextPackage
    claude_response: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ContextStatus(BaseModel):
    claude_configured: bool
    model: str | None
    token_budget: int
