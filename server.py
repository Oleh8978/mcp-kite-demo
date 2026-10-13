"""MCP demo server for the KITE AI Engineer presentation."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kite-demo-server")

SAFE_ROOT = Path.home() / "Projects"


def _resolve(path: str) -> Path:
    p = (SAFE_ROOT / path).resolve()
    if not str(p).startswith(str(SAFE_ROOT)):
        raise ValueError(f"path escapes safe root: {path}")
    return p


@mcp.tool()
def list_files(relative_path: str = ".") -> list[str]:
    """List entries of a directory under the safe root (~/Projects)."""
    target = _resolve(relative_path)
    if not target.is_dir():
        raise ValueError(f"not a directory: {relative_path}")
    return sorted(os.listdir(target))


@mcp.tool()
def read_text_file(relative_path: str, max_chars: int = 2000) -> str:
    """Read a UTF-8 text file under the safe root and return at most max_chars."""
    target = _resolve(relative_path)
    if not target.is_file():
        raise ValueError(f"not a file: {relative_path}")
    data = target.read_text(encoding="utf-8", errors="replace")
    return data[:max_chars]


@mcp.tool()
def word_count(text: str) -> int:
    """Count whitespace-separated words in the provided text."""
    return len(text.split())


@mcp.tool()
def keyword_scan(text: str, keywords: list[str]) -> dict[str, int]:
    """Count occurrences (case-insensitive) of each keyword in text."""
    low = text.lower()
    return {kw: low.count(kw.lower()) for kw in keywords}


if __name__ == "__main__":
    mcp.run()
