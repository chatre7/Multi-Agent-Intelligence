"""
ToolRun entity.

Represents a tool execution request with human-in-the-loop approval state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.value_objects.tool_run_status import ToolRunStatus


@dataclass
class ToolRun:
    """A requested tool execution."""

    id: str
    tool_id: str
    parameters: dict[str, Any]
    requested_by_role: str
    requires_approval: bool
    requested_by_sub: str = ""
    conversation_id: str = ""
    status: ToolRunStatus = ToolRunStatus.PENDING_APPROVAL
    approved_by_role: str | None = None
    approved_at: datetime | None = None
    rejected_by_role: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    executed_by_role: str | None = None
    executed_at: datetime | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def approve(self, role: str) -> None:
        """Approve this tool run."""
        if not self.requires_approval:
            pass
        elif self.status != ToolRunStatus.PENDING_APPROVAL:
            raise ValueError("Only pending tool runs can be approved.")

        self.status = ToolRunStatus.APPROVED
        self.approved_by_role = role
        self.approved_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def reject(self, role: str, reason: str) -> None:
        """Reject this tool run."""
        if not self.requires_approval:
            raise ValueError("Non-approvable tool runs cannot be rejected.")
        if self.status != ToolRunStatus.PENDING_APPROVAL:
            raise ValueError("Only pending tool runs can be rejected.")
        self.status = ToolRunStatus.REJECTED
        self.rejected_by_role = role
        self.rejected_at = datetime.now(UTC)
        self.rejection_reason = reason
        self.updated_at = datetime.now(UTC)

    def mark_executed(self, role: str, result: dict[str, Any]) -> None:
        """Mark this tool run executed with result payload."""
        self.status = ToolRunStatus.EXECUTED
        self.executed_by_role = role
        self.executed_at = datetime.now(UTC)
        self.result = dict(result)
        self.error = None
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, role: str, error: str) -> None:
        """Mark this tool run as failed."""
        self.status = ToolRunStatus.FAILED
        self.executed_by_role = role
        self.executed_at = datetime.now(UTC)
        self.error = error
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for APIs."""
        return {
            "id": self.id,
            "tool_id": self.tool_id,
            "parameters": dict(self.parameters),
            "requested_by_role": self.requested_by_role,
            "requested_by_sub": self.requested_by_sub,
            "conversation_id": self.conversation_id,
            "requires_approval": self.requires_approval,
            "status": self.status.value,
            "approved_by_role": self.approved_by_role,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by_role": self.rejected_by_role,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "executed_by_role": self.executed_by_role,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "result": dict(self.result),
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
