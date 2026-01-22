"""In-memory RegisteredAgent repository (MVP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from src.domain.entities.registered_agent import RegisteredAgent
from src.domain.repositories.registered_agent_repository import (
    IRegisteredAgentRepository,
)


@dataclass
class InMemoryRegisteredAgentRepository(IRegisteredAgentRepository):
    """Thread-safe in-memory repository for registered agents."""

    _by_id: dict[str, RegisteredAgent] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def upsert(self, agent: RegisteredAgent) -> None:
        with self._lock:
            self._by_id[agent.id] = agent

    def get(self, agent_id: str) -> RegisteredAgent | None:
        with self._lock:
            return self._by_id.get(agent_id)

    def list_all(self) -> list[RegisteredAgent]:
        with self._lock:
            agents = list(self._by_id.values())
        agents.sort(key=lambda a: (a.name, a.id))
        return agents
