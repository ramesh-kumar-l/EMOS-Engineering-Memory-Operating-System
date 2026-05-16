from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.exceptions import ClaudeNotConfiguredError, IndexNotReadyError
from ..memory.repository import MemoryRepository
from ..retrieval.embedder import Embedder
from ..retrieval.index import FAISSIndex
from ..retrieval.service import RetrievalService
from .client import AIClient
from .ranker import final_score, recency_score
from .schemas import (
    ContextChunk,
    ContextPackage,
    ContextRequest,
    ContextResponse,
    ContextStatus,
)

_OVERHEAD_TOKENS = 2_000  # budget reserved for system message and formatting
_CHARS_PER_TOKEN = 4       # ~4 chars/token for English prose (Claude approximation)


def _count_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _format_context(chunks: list[ContextChunk], query: str) -> str:
    """Render context as structured Markdown for Claude's system message."""
    parts = [f"# Retrieved Context for: {query}\n"]
    for i, chunk in enumerate(chunks, 1):
        cat_label = f" [{chunk.category}]" if chunk.category else ""
        parts.append(f"## {i}. {chunk.title}{cat_label}\n\n{chunk.content}")
    return "\n\n".join(parts)


class ContextService:
    def __init__(
        self,
        db: Session,
        embedder: Embedder,
        index: FAISSIndex,
        claude: AIClient | None,
    ) -> None:
        self._repo = MemoryRepository(db)
        self._retrieval = RetrievalService(db, embedder, index)
        self._claude = claude

    def assemble(self, req: ContextRequest) -> ContextResponse:
        if req.send_to_claude and self._claude is None:
            raise ClaudeNotConfiguredError()

        results = self._retrieval.search(
            query=req.query,
            limit=req.max_chunks * 2,  # over-fetch; trimmed by budget below
            alpha=req.alpha,
            mode=req.mode,
        )

        # Fetch full docs and compute combined relevance+recency score
        candidates: list[tuple[object, float, float, float]] = []  # (doc, relevance, recency, final)
        for result in results.items:
            doc = self._repo.get_by_slug(result.slug)
            if doc is None:
                continue
            r_score = recency_score(doc.updated_at)
            f_score = final_score(result.score, r_score, req.recency_weight)
            candidates.append((doc, result.score, r_score, f_score))

        candidates.sort(key=lambda x: x[3], reverse=True)

        usable_budget = max(0, req.token_budget - _OVERHEAD_TOKENS)
        chunks: list[ContextChunk] = []
        used_tokens = 0

        for doc, rel_score, rec_score, f_score in candidates:
            if len(chunks) >= req.max_chunks:
                break

            token_count = _count_tokens(doc.content)
            content = doc.content

            if used_tokens + token_count > usable_budget:
                available_chars = (usable_budget - used_tokens) * _CHARS_PER_TOKEN
                if available_chars < 400:  # less than ~100 tokens — not worth including
                    break
                content = doc.content[:available_chars]
                token_count = _count_tokens(content)

            chunks.append(ContextChunk(
                slug=doc.slug,
                title=doc.title,
                category=doc.category if doc.category != "general" else None,
                content=content,
                relevance_score=round(rel_score, 4),
                recency_score=round(rec_score, 4),
                final_score=round(f_score, 4),
                token_count=token_count,
            ))
            used_tokens += token_count

            if content != doc.content:  # truncated — budget exhausted
                break

        package = ContextPackage(
            query=req.query,
            chunks=chunks,
            total_tokens=used_tokens,
            token_budget=req.token_budget,
            budget_used_pct=round(used_tokens / req.token_budget * 100, 1) if req.token_budget else 0.0,
        )

        if not req.send_to_claude:
            return ContextResponse(package=package)

        context_text = _format_context(chunks, req.query)
        system_prompt = (
            "You are EMOS — an Engineering Memory Operating System assistant. "
            "Answer the user's question using only the context provided below. "
            "If the context does not contain the answer, say so explicitly. "
            "Do not invent facts, APIs, or file paths that are not present in the context.\n\n"
            f"{context_text}"
        )
        user_prompt = req.claude_prompt or req.query
        response_text, input_tok, output_tok = self._claude.complete(system_prompt, user_prompt)

        return ContextResponse(
            package=package,
            claude_response=response_text,
            model=self._claude.model,
            input_tokens=input_tok,
            output_tokens=output_tok,
        )

    def status(self) -> ContextStatus:
        settings = get_settings()
        return ContextStatus(
            claude_configured=self._claude is not None,
            model=self._claude.model if self._claude is not None else None,
            token_budget=settings.token_budget,
        )
