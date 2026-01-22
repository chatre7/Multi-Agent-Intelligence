"""TDD tests for filesystem tool handlers."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest


def _workspace_tmp_dir() -> Path:
    root = Path.cwd() / ".test_tmp" / f"file_tools_{uuid4()}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_save_file_writes_under_root() -> None:
    import os

    root = _workspace_tmp_dir()
    os.environ["TOOL_FILE_ROOT"] = str(root)

    from src.infrastructure.tools.file_tools import save_file

    result = save_file(path="notes/hello.txt", content="hi")
    assert result["ok"] is True

    expected_path = root / "notes" / "hello.txt"
    assert expected_path.exists()
    assert expected_path.read_text(encoding="utf-8") == "hi"


@pytest.mark.parametrize(
    "bad_path",
    [
        "../secrets.txt",
        "..\\secrets.txt",
        "/etc/passwd",
        "C:\\Windows\\system.ini",
    ],
)
def test_save_file_rejects_path_traversal_and_absolute_paths(bad_path: str) -> None:
    import os

    root = _workspace_tmp_dir()
    os.environ["TOOL_FILE_ROOT"] = str(root)

    from src.infrastructure.tools.file_tools import save_file

    with pytest.raises(ValueError, match="Invalid path"):
        save_file(path=bad_path, content="x")
