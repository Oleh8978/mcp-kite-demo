"""MCP demo server for the KITE AI Engineer reference project.

Pure helpers (testable) plus a thin MCP wrapper.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

SAFE_ROOT: Path = Path.home() / "Projects"


def resolve_safe(path: str, safe_root: Path | None = None) -> Path:
    """Resolve path under safe_root and reject anything that escapes it."""
    root = (safe_root or SAFE_ROOT).resolve()
    target = (root / path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes safe root: {path}")
    return target


def list_files_impl(relative_path: str = ".", safe_root: Path | None = None) -> list[str]:
    target = resolve_safe(relative_path, safe_root)
    if not target.is_dir():
        raise ValueError(f"not a directory: {relative_path}")
    return sorted(os.listdir(target))


def read_text_file_impl(
    relative_path: str, max_chars: int = 2000, safe_root: Path | None = None
) -> str:
    target = resolve_safe(relative_path, safe_root)
    if not target.is_file():
        raise ValueError(f"not a file: {relative_path}")
    data = target.read_text(encoding="utf-8", errors="replace")
    return data[:max_chars]


def word_count_impl(text: str) -> int:
    return len(text.split())


def keyword_scan_impl(text: str, keywords: list[str]) -> dict[str, int]:
    low = text.lower()
    return {kw: low.count(kw.lower()) for kw in keywords}


mcp = FastMCP("kite-demo-server")


@mcp.tool()
def list_files(relative_path: str = ".") -> list[str]:
    """List entries of a directory under the safe root (~/Projects)."""
    return list_files_impl(relative_path)


@mcp.tool()
def read_text_file(relative_path: str, max_chars: int = 2000) -> str:
    """Read a UTF-8 text file under the safe root, capped at max_chars."""
    return read_text_file_impl(relative_path, max_chars)


@mcp.tool()
def word_count(text: str) -> int:
    """Count whitespace-separated words in the provided text."""
    return word_count_impl(text)


@mcp.tool()
def keyword_scan(text: str, keywords: list[str]) -> dict[str, int]:
    """Count case-insensitive occurrences of each keyword in text."""
    return keyword_scan_impl(text, keywords)


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
