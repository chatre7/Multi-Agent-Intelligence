"""
Conversation entity.

Represents a chat session grouping messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ThreadStatus(str, Enum):
    """Status of a conversation thread (PR-style)."""
    OPEN = "open"
    REVIEW_REQUESTED = "review_requested"
    MERGED = "merged"
    CLOSED = "closed"


@dataclass
class Conversation:
    """Conversation aggregate root (MVP)."""

    id: str
    domain_id: str
    created_by_role: str
    created_by_sub: str = ""
    title: str | None = None
    status: ThreadStatus = ThreadStatus.OPEN
    reviewers: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain_id": self.domain_id,
            "created_by_role": self.created_by_role,
            "created_by_sub": self.created_by_sub,
            "title": self.title,
            "status": self.status.value,
            "reviewers": self.reviewers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
            "messages": [],  # Default empty messages for frontend compatibility
        }
