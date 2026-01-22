"""File operation tool handlers.

These handlers are intended to be used via configuration (Tool.handler_path) and
must be safe by default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _tool_root() -> Path:
    configured = os.getenv("TOOL_FILE_ROOT")
    if configured:
        return Path(configured)
    return Path.cwd() / ".tool_files"


def _safe_relative_path(value: str) -> Path:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Invalid path: empty")

    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError("Invalid path: must be relative")

    # Block Windows drive paths like C:\...
    if candidate.drive:
        raise ValueError("Invalid path: must not include drive")

    # Block traversal and parent references
    for part in candidate.parts:
        if part in {"..", ""}:
            raise ValueError("Invalid path: traversal not allowed")

    return candidate


def save_file(path: str, content: str) -> dict[str, Any]:
    """Save a file under TOOL_FILE_ROOT.

    Parameters
    ----------
    path : str
        Relative path to write under TOOL_FILE_ROOT.
    content : str
        File contents.

    Returns
    -------
    dict[str, Any]
        Result payload.
    """
    root = _tool_root()
    rel = _safe_relative_path(path)
    target = (root / rel).resolve()

    # Ensure target stays under root
    root_resolved = root.resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("Invalid path: outside root") from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": str(rel).replace("\\", "/")}
