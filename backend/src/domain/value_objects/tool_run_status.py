"""
ToolRunStatus value object.

Defines the lifecycle of a tool execution request.
"""

from __future__ import annotations

from enum import Enum


class ToolRunStatus(Enum):
    """Status values for a tool run."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

    @classmethod
    def from_string(cls, value: str) -> ToolRunStatus:
        """Parse status from string."""
        value_lower = value.lower().strip()
        for status in cls:
            if status.value == value_lower:
                return status
        valid = [s.value for s in cls]
        raise ValueError(f"Invalid tool run status: '{value}'. Valid: {valid}")

    def __str__(self) -> str:
        return self.value
