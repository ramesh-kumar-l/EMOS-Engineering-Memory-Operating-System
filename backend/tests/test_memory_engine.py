from pathlib import Path

import pytest

from ..memory.engine import MemoryBankEngine, compute_checksum, count_words


def test_write_creates_file(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("my-doc", "My Doc", "Hello world.")
    assert (tmp_path / "my-doc.md").exists()


def test_read_returns_correct_fields(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("alpha", "Alpha Title", "Body text here.", "core", ["tag1", "tag2"])
    doc = engine.read("alpha")

    assert doc.slug == "alpha"
    assert doc.title == "Alpha Title"
    assert doc.content == "Body text here."
    assert doc.category == "core"
    assert "tag1" in doc.tags
    assert doc.word_count == 3


def test_read_missing_raises(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    with pytest.raises(FileNotFoundError):
        engine.read("does-not-exist")


def test_delete_removes_file(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("del-me", "Delete Me", "bye")
    engine.delete("del-me")
    assert not (tmp_path / "del-me.md").exists()


def test_delete_missing_raises(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    with pytest.raises(FileNotFoundError):
        engine.delete("ghost")


def test_list_slugs(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("aaa", "AAA", "a")
    engine.write("bbb", "BBB", "b")
    assert set(engine.list_slugs()) == {"aaa", "bbb"}


def test_overwrite_updates_content(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("doc", "Old Title", "old content")
    engine.write("doc", "New Title", "new content")
    doc = engine.read("doc")
    assert doc.title == "New Title"
    assert doc.content == "new content"


def test_checksum_is_stable() -> None:
    assert compute_checksum("x") == compute_checksum("x")
    assert compute_checksum("x") != compute_checksum("y")


def test_word_count() -> None:
    assert count_words("one two three") == 3
    assert count_words("") == 0


def test_read_all_skips_corrupt(tmp_path: Path) -> None:
    engine = MemoryBankEngine(tmp_path)
    engine.write("good", "Good", "content")
    # Write a file that cannot be parsed as UTF-8
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe")
    docs = engine.read_all()
    assert any(d.slug == "good" for d in docs)
