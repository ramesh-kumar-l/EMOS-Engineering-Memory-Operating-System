from pydantic import BaseModel


class RetrievalResult(BaseModel):
    slug: str
    title: str
    category: str
    score: float
    keyword_score: float | None = None
    semantic_score: float | None = None
    content_preview: str


class RetrievalResponse(BaseModel):
    total: int
    query: str
    mode: str
    items: list[RetrievalResult]


class IndexStatus(BaseModel):
    total_indexed: int
    total_documents: int
    index_size_bytes: int


class IndexResponse(BaseModel):
    indexed: int
    message: str
