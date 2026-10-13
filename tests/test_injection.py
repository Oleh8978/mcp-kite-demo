"""Tests for the path guard against prompt-injection style content.

The server does not interpret file content. The only defense that
matters is that no tool call can escape the safe root, even if an LLM
that reads the file decides to follow the injection.
"""

from pathlib import Path

import pytest

from kite_agent import server


def test_guard_blocks_ssh_relative_path(tmp_path: Path):
    with pytest.raises(ValueError):
        server.resolve_safe("../.ssh/id_ed25519", safe_root=tmp_path)


def test_guard_blocks_absolute_path(tmp_path: Path):
    with pytest.raises(ValueError):
        server.resolve_safe("/etc/passwd", safe_root=tmp_path)


def test_guard_blocks_deep_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        server.resolve_safe("../../../etc/passwd", safe_root=tmp_path)


def test_guard_blocks_user_config_path(tmp_path: Path):
    with pytest.raises(ValueError):
        server.resolve_safe("../.config", safe_root=tmp_path)


def test_server_reads_injection_file_without_acting_on_it(tmp_path: Path):
    fixture = Path(__file__).parent / "fixtures" / "injected_notes.md"
    target_dir = tmp_path / "notes"
    target_dir.mkdir()
    (target_dir / "injected_notes.md").write_text(fixture.read_text(encoding="utf-8"))

    content = server.read_text_file_impl("notes/injected_notes.md", safe_root=tmp_path)
    assert "Ignore all previous instructions" in content
    assert "../.ssh/id_ed25519" in content
