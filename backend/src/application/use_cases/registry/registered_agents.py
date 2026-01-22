"""Use cases for the agent registry (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.registered_agent import RegisteredAgent
from src.domain.repositories.registered_agent_repository import (
    IRegisteredAgentRepository,
)
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


@dataclass(frozen=True)
class RegisterAgentRequest:
    id: str
    name: str
    description: str
    endpoint: str
    version: str
    state: str
    capabilities: list[str]


@dataclass
class RegisterAgentUseCase:
    repo: IRegisteredAgentRepository

    def execute(self, request: RegisterAgentRequest) -> RegisteredAgent:
        if not request.id.strip():
            raise ValueError("id is required")
        if not request.name.strip():
            raise ValueError("name is required")
        version = SemanticVersion.from_string(request.version)
        state = AgentState.from_string(request.state)
        agent = RegisteredAgent(
            id=request.id.strip(),
            name=request.name.strip(),
            description=request.description.strip(),
            endpoint=str(request.endpoint or "").strip(),
            version=version,
            state=state,
            capabilities=list(request.capabilities or []),
        )
        self.repo.upsert(agent)
        return agent


@dataclass(frozen=True)
class PromoteRegisteredAgentRequest:
    agent_id: str
    state: str


@dataclass
class PromoteRegisteredAgentUseCase:
    repo: IRegisteredAgentRepository

    def execute(self, request: PromoteRegisteredAgentRequest) -> RegisteredAgent:
        agent = self.repo.get(request.agent_id)
        if agent is None:
            raise ValueError("Unknown agent_id")
        target = AgentState.from_string(request.state)
        agent.promote(target)
        self.repo.upsert(agent)
        return agent


@dataclass(frozen=True)
class BumpAgentVersionRequest:
    agent_id: str
    kind: str


@dataclass
class BumpAgentVersionUseCase:
    repo: IRegisteredAgentRepository

    def execute(self, request: BumpAgentVersionRequest) -> RegisteredAgent:
        agent = self.repo.get(request.agent_id)
        if agent is None:
            raise ValueError("Unknown agent_id")
        agent.bump_version(request.kind)
        self.repo.upsert(agent)
        return agent


@dataclass(frozen=True)
class ListRegisteredAgentsRequest:
    pass


@dataclass
class ListRegisteredAgentsUseCase:
    repo: IRegisteredAgentRepository

    def execute(
        self, request: ListRegisteredAgentsRequest | None = None
    ) -> list[RegisteredAgent]:
        _ = request
        return self.repo.list_all()


@dataclass(frozen=True)
class GetRegisteredAgentRequest:
    agent_id: str


@dataclass
class GetRegisteredAgentUseCase:
    repo: IRegisteredAgentRepository

    def execute(self, request: GetRegisteredAgentRequest) -> RegisteredAgent:
        agent = self.repo.get(request.agent_id)
        if agent is None:
            raise ValueError("Unknown agent_id")
        return agent
