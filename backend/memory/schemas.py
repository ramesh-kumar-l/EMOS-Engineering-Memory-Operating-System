from datetime import datetime
from pydantic import BaseModel, Field


class DocumentContent(BaseModel):
    """Internal transfer object produced by MemoryBankEngine."""
    slug: str
    title: str
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    file_path: str
    checksum: str
    word_count: int


class DocumentCreate(BaseModel):
    slug: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", max_length=255,
                      description="URL-safe lowercase slug, e.g. 'architecture-overview'")
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field(default="general", max_length=100)
    tags: list[str] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    content: str | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    slug: str
    title: str
    content: str
    category: str
    tags: list[str]
    file_path: str
    checksum: str
    word_count: int
    is_indexed: bool
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]


class SyncResponse(BaseModel):
    synced: int
    message: str
