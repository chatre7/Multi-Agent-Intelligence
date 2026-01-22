"""Shared helpers for tool-run use cases."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any


def load_handler(handler_path: str) -> Callable[..., Any]:
    """Load a handler function from a dotted module path `pkg.mod.func`."""
    module_path, function_name = _split_handler_path(handler_path)
    module = import_module(module_path)
    handler = getattr(module, function_name, None)
    if handler is None or not callable(handler):
        raise ImportError(f"Handler not found or not callable: {handler_path}")
    return handler


def _split_handler_path(handler_path: str) -> tuple[str, str]:
    if "." not in handler_path:
        raise ValueError(f"Invalid handler_path: {handler_path}")
    module_path, function_name = handler_path.rsplit(".", 1)
    return module_path, function_name


def normalize_result(value: Any) -> dict[str, Any]:
    """Ensure tool handler result is a JSON-serializable mapping."""
    if isinstance(value, dict):
        return dict(value)
    return {"ok": True, "value": value}
