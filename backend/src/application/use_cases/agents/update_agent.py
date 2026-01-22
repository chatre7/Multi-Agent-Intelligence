"""
Update Agent Use Case.

Handles modification of existing agent configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository


@dataclass
class UpdateAgentRequest:
    """Request to update an agent."""

    agent_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[list[str]] = None
    tools: Optional[list[str]] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[float] = None
    keywords: Optional[list[str]] = None
    priority: Optional[int] = None


@dataclass
class UpdateAgentResponse:
    """Response from updating an agent."""

    agent: Agent


class UpdateAgentUseCase:
    """Use case for updating an existing agent."""

    def __init__(self, agent_repo: IAgentRepository):
        """
        Initialize use case.

        Parameters
        ----------
        agent_repo : IAgentRepository
            Agent repository for persistence.
        """
        self.agent_repo = agent_repo

    async def execute(self, request: UpdateAgentRequest) -> UpdateAgentResponse:
        """
        Execute the update agent use case.

        Parameters
        ----------
        request : UpdateAgentRequest
            The update request.

        Returns
        -------
        UpdateAgentResponse
            The updated agent.

        Raises
        ------
        ValueError
            If validation fails or agent not found.
        """
        # Find agent
        agent = await self.agent_repo.find_by_id(request.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID '{request.agent_id}' not found")

        # Update fields if provided
        if request.name is not None:
            if not request.name.strip():
                raise ValueError("Agent name cannot be empty")
            agent.name = request.name

        if request.description is not None:
            agent.description = request.description

        if request.system_prompt is not None:
            if not request.system_prompt.strip():
                raise ValueError("System prompt cannot be empty")
            agent.system_prompt = request.system_prompt

        if request.capabilities is not None:
            if not request.capabilities:
                raise ValueError("Agent must have at least one capability")
            agent.capabilities = request.capabilities

        if request.tools is not None:
            agent.tools = request.tools

        if request.model_name is not None:
            agent.model_name = request.model_name

        if request.temperature is not None:
            if request.temperature < 0 or request.temperature > 1:
                raise ValueError("Temperature must be between 0 and 1")
            agent.temperature = request.temperature

        if request.max_tokens is not None:
            if request.max_tokens < 1:
                raise ValueError("Max tokens must be at least 1")
            agent.max_tokens = request.max_tokens

        if request.timeout_seconds is not None:
            if request.timeout_seconds < 1:
                raise ValueError("Timeout must be at least 1 second")
            agent.timeout_seconds = request.timeout_seconds

        if request.keywords is not None:
            agent.keywords = request.keywords

        if request.priority is not None:
            agent.priority = request.priority

        # Persist
        saved_agent = await self.agent_repo.save(agent)

        return UpdateAgentResponse(agent=saved_agent)
