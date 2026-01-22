"""No-op tool handler used as a safe default for missing handlers."""

from __future__ import annotations

from typing import Any


def noop(**kwargs: Any) -> dict[str, Any]:
    """Return inputs back to the caller.

    Parameters
    ----------
    **kwargs : Any
        Arbitrary tool parameters.

    Returns
    -------
    dict[str, Any]
        Echo payload.
    """
    return {"ok": True, "echo": dict(kwargs)}
