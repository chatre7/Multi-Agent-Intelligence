"""RegisteredAgent entity.

Represents a runtime-discovered agent (local or remote) registered with the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


@dataclass
class RegisteredAgent:
    """An agent registration record."""

    id: str
    name: str
    description: str
    endpoint: str
    version: SemanticVersion
    state: AgentState
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def promote(self, target_state: AgentState) -> None:
        """Transition lifecycle state if allowed."""
        if not self.state.can_transition_to(target_state):
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {target_state.value}"
            )
        self.state = target_state
        self.updated_at = datetime.now(UTC)

    def heartbeat(self) -> None:
        """Mark this agent as recently alive."""
        now = datetime.now(UTC)
        self.last_heartbeat_at = now
        self.updated_at = now

    def bump_version(self, kind: str) -> None:
        """Bump semantic version.

        Parameters
        ----------
        kind : str
            One of: 'patch', 'minor', 'major'.
        """
        kind_lower = (kind or "").lower().strip()
        if kind_lower == "patch":
            self.version = self.version.increment_patch()
        elif kind_lower == "minor":
            self.version = self.version.increment_minor()
        elif kind_lower == "major":
            self.version = self.version.increment_major()
        else:
            raise ValueError("kind must be one of: patch, minor, major")
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "version": str(self.version),
            "state": self.state.value,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
            "last_heartbeat_at": self.last_heartbeat_at.isoformat()
            if self.last_heartbeat_at
            else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
