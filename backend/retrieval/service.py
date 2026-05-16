import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.exceptions import IndexNotReadyError
from ..memory.repository import MemoryRepository
from .embedder import Embedder
from .index import FAISSIndex
from .schemas import IndexResponse, IndexStatus, RetrievalResponse, RetrievalResult

_DEFAULT_ALPHA = 0.5
_PREVIEW_LEN = 200


class RetrievalService:
    def __init__(self, db: Session, embedder: Embedder, index: FAISSIndex) -> None:
        self.db = db
        self.repo = MemoryRepository(db)
        self.embedder = embedder
        self.index = index

    def search(
        self,
        query: str,
        limit: int = 20,
        alpha: float = _DEFAULT_ALPHA,
        mode: str = "hybrid",
    ) -> RetrievalResponse:
        if mode in ("hybrid", "semantic") and not self.index.is_built():
            raise IndexNotReadyError()

        keyword_scores: dict[str, float] = {}
        semantic_scores: dict[str, float] = {}

        if mode in ("hybrid", "keyword"):
            keyword_scores = self._fts_scores(query, limit * 2)

        if mode in ("hybrid", "semantic"):
            vec = self.embedder.encode_one(query)
            semantic_scores = dict(self.index.search(vec, limit * 2))

        all_slugs = set(keyword_scores) | set(semantic_scores)
        fused: list[tuple[str, float, float, float]] = []

        for slug in all_slugs:
            ks = keyword_scores.get(slug, 0.0)
            ss = semantic_scores.get(slug, 0.0)
            if mode == "keyword":
                total = ks
            elif mode == "semantic":
                total = ss
            else:
                total = alpha * ss + (1 - alpha) * ks
            fused.append((slug, total, ks, ss))

        fused.sort(key=lambda x: x[1], reverse=True)
        fused = fused[:limit]

        items = []
        for slug, score, ks, ss in fused:
            doc = self.repo.get_by_slug(slug)
            if doc is None:
                continue
            items.append(RetrievalResult(
                slug=slug,
                title=doc.title,
                category=doc.category,
                score=round(score, 4),
                keyword_score=round(ks, 4) if mode != "semantic" else None,
                semantic_score=round(ss, 4) if mode != "keyword" else None,
                content_preview=doc.content[:_PREVIEW_LEN],
            ))

        return RetrievalResponse(total=len(items), query=query, mode=mode, items=items)

    def build_index(self) -> IndexResponse:
        """Embed all documents and rebuild FAISS index from scratch."""
        all_docs = self.repo.list_all(limit=10_000, offset=0)
        if not all_docs:
            return IndexResponse(indexed=0, message="No documents to index.")
        texts = [f"{d.title} {d.content}" for d in all_docs]
        slugs = [d.slug for d in all_docs]
        vectors = self.embedder.encode(texts)
        self.index.build(vectors, slugs)
        for doc in all_docs:
            doc.is_indexed = True
        self.db.commit()
        return IndexResponse(indexed=len(all_docs), message=f"Indexed {len(all_docs)} document(s).")

    def index_status(self) -> IndexStatus:
        return IndexStatus(
            total_indexed=self.index.size(),
            total_documents=self.repo.count(),
            index_size_bytes=self.index.index_size_bytes(),
        )

    def _fts_scores(self, query: str, limit: int) -> dict[str, float]:
        """Normalised BM25 scores: 1.0 = best match, 0.0 = weakest match in result set."""
        rows = self.db.execute(
            text("SELECT slug, rank FROM memory_fts WHERE memory_fts MATCH :q ORDER BY rank LIMIT :lim"),
            {"q": query, "lim": limit},
        ).fetchall()
        if not rows:
            return {}
        # FTS5 rank is negative; most negative = most relevant.
        ranks = [r[1] for r in rows]
        min_r, max_r = min(ranks), max(ranks)
        if min_r == max_r:
            return {row[0]: 1.0 for row in rows}
        span = max_r - min_r
        return {row[0]: (max_r - row[1]) / span for row in rows}
