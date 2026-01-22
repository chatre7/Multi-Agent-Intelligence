"""Get Agent Details Use Case."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository


@dataclass
class GetAgentRequest:
    """Request to get agent details."""

    agent_id: str


@dataclass
class GetAgentResponse:
    """Response with agent details."""

    agent: Agent


class GetAgentUseCase:
    """Use case for retrieving agent details."""

    def __init__(self, agent_repo: IAgentRepository):
        self.agent_repo = agent_repo

    async def execute(self, request: GetAgentRequest) -> GetAgentResponse:
        """Get agent by ID."""
        agent = await self.agent_repo.find_by_id(request.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID '{request.agent_id}' not found")

        return GetAgentResponse(agent=agent)
