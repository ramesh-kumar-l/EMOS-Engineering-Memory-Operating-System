import json
from pathlib import Path

import faiss
import numpy as np

_INDEX_FILE = "memory.faiss"
_META_FILE = "memory_meta.json"


class FAISSIndex:
    """
    Flat inner-product index over L2-normalised vectors — equivalent to cosine similarity.
    Persisted to disk under index_dir. Full rebuild on every build() call (suitable for ≤10k docs).
    """

    def __init__(self, index_dir: Path) -> None:
        self._dir = index_dir
        self._index: faiss.IndexFlatIP | None = None
        self._slugs: list[str] = []
        self._loaded = False

    @property
    def _index_path(self) -> Path:
        return self._dir / _INDEX_FILE

    @property
    def _meta_path(self) -> Path:
        return self._dir / _META_FILE

    def build(self, vectors: np.ndarray, slugs: list[str]) -> None:
        """Build index from scratch and persist to disk."""
        if len(vectors) == 0:
            self._index = None
            self._slugs = []
            self._loaded = True
            return
        dim = vectors.shape[1]
        idx = faiss.IndexFlatIP(dim)
        idx.add(vectors)
        self._index = idx
        self._slugs = list(slugs)
        self._loaded = True
        self._save()

    def search(self, query_vector: np.ndarray, k: int) -> list[tuple[str, float]]:
        """Return (slug, cosine_score) pairs sorted descending by score."""
        self._ensure_loaded()
        if self._index is None or self._index.ntotal == 0:
            return []
        k = min(k, self._index.ntotal)
        scores, indices = self._index.search(query_vector.reshape(1, -1), k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self._slugs):
                results.append((self._slugs[idx], float(score)))
        return results

    def size(self) -> int:
        self._ensure_loaded()
        return self._index.ntotal if self._index else 0

    def is_built(self) -> bool:
        """Returns True if a persisted index exists on disk."""
        return self._index_path.exists()

    def index_size_bytes(self) -> int:
        return self._index_path.stat().st_size if self._index_path.exists() else 0

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self._index_path.exists() and self._meta_path.exists():
            self._index = faiss.read_index(str(self._index_path))
            with open(self._meta_path, encoding="utf-8") as f:
                self._slugs = json.load(f)
        self._loaded = True

    def _save(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        if self._index is not None:
            faiss.write_index(self._index, str(self._index_path))
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(self._slugs, f)
