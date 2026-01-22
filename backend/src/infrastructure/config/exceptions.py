"""Configuration loading errors."""

from __future__ import annotations


class ConfigError(Exception):
    """Base error for configuration loading/processing."""


class ConfigValidationError(ConfigError):
    """Raised when a configuration document fails validation."""

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message)
        self.path = path
