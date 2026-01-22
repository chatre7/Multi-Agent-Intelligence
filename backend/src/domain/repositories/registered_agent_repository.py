"""Repository interface for registered agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.registered_agent import RegisteredAgent


class IRegisteredAgentRepository(ABC):
    """Port for storing registered agents."""

    @abstractmethod
    def upsert(self, agent: RegisteredAgent) -> None:
        """Insert or update a registered agent."""

    @abstractmethod
    def get(self, agent_id: str) -> RegisteredAgent | None:
        """Fetch an agent by id."""

    @abstractmethod
    def list_all(self) -> list[RegisteredAgent]:
        """List all registered agents."""
