"""List Agents Use Case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_state import AgentState


@dataclass
class ListAgentsRequest:
    """Request to list agents."""

    domain_id: Optional[str] = None
    state: Optional[AgentState] = None
    active_only: bool = False


@dataclass
class ListAgentsResponse:
    """Response from listing agents."""

    agents: list[Agent]
    count: int


class ListAgentsUseCase:
    """Use case for listing agents."""

    def __init__(self, agent_repo: IAgentRepository):
        self.agent_repo = agent_repo

    async def execute(self, request: ListAgentsRequest) -> ListAgentsResponse:
        """List agents with optional filters."""
        if request.active_only:
            agents = await self.agent_repo.find_active()
        elif request.state:
            agents = await self.agent_repo.find_by_state(request.state)
        elif request.domain_id:
            agents = await self.agent_repo.find_by_domain(request.domain_id)
        else:
            agents = await self.agent_repo.find_all()

        return ListAgentsResponse(agents=agents, count=len(agents))
