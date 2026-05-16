from pathlib import Path

import numpy as np
import pytest

from ..retrieval.index import FAISSIndex


def _make_vecs(n: int, dim: int = 16, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vecs = rng.random((n, dim), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


def test_faiss_build_and_search(tmp_path: Path) -> None:
    index = FAISSIndex(tmp_path)
    slugs = ["doc-a", "doc-b", "doc-c"]
    vecs = _make_vecs(3)
    index.build(vecs, slugs)
    results = index.search(vecs[0], k=3)
    assert results[0][0] == "doc-a"
    assert results[0][1] > 0.99


def test_faiss_persistence(tmp_path: Path) -> None:
    vecs = _make_vecs(2)
    FAISSIndex(tmp_path).build(vecs, ["x", "y"])
    loaded = FAISSIndex(tmp_path)
    results = loaded.search(vecs[0], k=2)
    assert results[0][0] == "x"


def test_faiss_size_before_build(tmp_path: Path) -> None:
    assert FAISSIndex(tmp_path).size() == 0


def test_faiss_size_after_build(tmp_path: Path) -> None:
    idx = FAISSIndex(tmp_path)
    idx.build(_make_vecs(3), ["a", "b", "c"])
    assert idx.size() == 3


def test_faiss_is_built(tmp_path: Path) -> None:
    idx = FAISSIndex(tmp_path)
    assert not idx.is_built()
    idx.build(_make_vecs(1), ["only"])
    assert idx.is_built()


def test_faiss_search_empty_index(tmp_path: Path) -> None:
    results = FAISSIndex(tmp_path).search(_make_vecs(1)[0], k=5)
    assert results == []


def test_faiss_k_capped_at_index_size(tmp_path: Path) -> None:
    idx = FAISSIndex(tmp_path)
    idx.build(_make_vecs(2), ["a", "b"])
    results = idx.search(_make_vecs(1, seed=99)[0], k=100)
    assert len(results) <= 2


def test_faiss_build_empty(tmp_path: Path) -> None:
    idx = FAISSIndex(tmp_path)
    idx.build(np.empty((0, 16), dtype=np.float32), [])
    assert idx.size() == 0
