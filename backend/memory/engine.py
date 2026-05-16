import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from ..core.config import get_settings
from .schemas import DocumentContent

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta = yaml.safe_load(match.group(1)) or {}
    body = raw[match.end():]
    return meta, body


def _render(meta: dict[str, Any], body: str) -> str:
    front = yaml.dump(meta, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{front}\n---\n{body}"


def compute_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def count_words(text: str) -> int:
    return len(text.split())


class MemoryBankEngine:
    """Reads and writes Markdown files. SQLite is a cache — Markdown is truth."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or get_settings().memory_bank_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slug: str) -> Path:
        return self.base_dir / f"{slug}.md"

    def exists(self, slug: str) -> bool:
        return self._path(slug).exists()

    def read(self, slug: str) -> DocumentContent:
        path = self._path(slug)
        if not path.exists():
            raise FileNotFoundError(f"Document '{slug}' not found at {path}")
        raw = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        return DocumentContent(
            slug=slug,
            title=meta.get("title") or slug.replace("-", " ").title(),
            content=body,
            category=str(meta.get("category", "general")),
            tags=list(meta.get("tags", [])),
            file_path=str(path),
            checksum=compute_checksum(raw),
            word_count=count_words(body),
        )

    def write(
        self,
        slug: str,
        title: str,
        body: str,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> DocumentContent:
        meta: dict[str, Any] = {
            "slug": slug,
            "title": title,
            "category": category,
            "tags": tags or [],
        }
        raw = _render(meta, body)
        self._path(slug).write_text(raw, encoding="utf-8")
        return DocumentContent(
            slug=slug,
            title=title,
            content=body,
            category=category,
            tags=tags or [],
            file_path=str(self._path(slug)),
            checksum=compute_checksum(raw),
            word_count=count_words(body),
        )

    def delete(self, slug: str) -> None:
        path = self._path(slug)
        if not path.exists():
            raise FileNotFoundError(f"Document '{slug}' not found")
        path.unlink()

    def list_slugs(self) -> list[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.md"))

    def read_all(self) -> list[DocumentContent]:
        docs = []
        for slug in self.list_slugs():
            try:
                docs.append(self.read(slug))
            except Exception:
                pass  # skip files that cannot be parsed
        return docs
