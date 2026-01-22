"""Delete Agent Use Case."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.agent_repository import IAgentRepository


@dataclass
class DeleteAgentRequest:
    """Request to delete an agent."""

    agent_id: str


@dataclass
class DeleteAgentResponse:
    """Response from deleting an agent."""

    deleted: bool
    message: str


class DeleteAgentUseCase:
    """Use case for deleting an agent."""

    def __init__(self, agent_repo: IAgentRepository):
        self.agent_repo = agent_repo

    async def execute(self, request: DeleteAgentRequest) -> DeleteAgentResponse:
        """Delete an agent by ID."""
        agent = await self.agent_repo.find_by_id(request.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID '{request.agent_id}' not found")

        deleted = await self.agent_repo.delete(request.agent_id)

        return DeleteAgentResponse(
            deleted=deleted,
            message=f"Agent '{request.agent_id}' deleted successfully"
            if deleted
            else "Failed to delete agent",
        )
