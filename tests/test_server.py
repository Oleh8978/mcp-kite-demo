from pathlib import Path

import pytest

from kite_agent import server


def test_resolve_rejects_escape(tmp_path: Path):
    with pytest.raises(ValueError):
        server.resolve_safe("../etc/passwd", safe_root=tmp_path)


def test_resolve_accepts_nested(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    assert server.resolve_safe("sub", safe_root=tmp_path) == (tmp_path / "sub").resolve()


def test_list_files(tmp_path: Path):
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    assert server.list_files_impl(".", safe_root=tmp_path) == ["a.txt", "b.txt"]


def test_list_files_rejects_file(tmp_path: Path):
    (tmp_path / "a.txt").write_text("x")
    with pytest.raises(ValueError):
        server.list_files_impl("a.txt", safe_root=tmp_path)


def test_read_truncates(tmp_path: Path):
    (tmp_path / "long.txt").write_text("x" * 500)
    assert len(server.read_text_file_impl("long.txt", 100, tmp_path)) == 100


def test_word_count():
    assert server.word_count_impl("a b c") == 3
    assert server.word_count_impl("") == 0


def test_keyword_scan_case_insensitive():
    assert server.keyword_scan_impl("Tool tool TOOL def", ["tool", "def"]) == {
        "tool": 3,
        "def": 1,
    }
