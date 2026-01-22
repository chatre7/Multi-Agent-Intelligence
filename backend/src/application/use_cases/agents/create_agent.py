"""
Create Agent Use Case.

Handles creation of new agents with validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


@dataclass
class CreateAgentRequest:
    """Request to create a new agent."""

    id: str
    name: str
    domain_id: str
    description: str
    system_prompt: str
    capabilities: list[str]
    tools: list[str]
    model_name: str = "gpt-oss:120b-cloud"
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    keywords: list[str] | None = None
    priority: int = 0
    author: str = "system"


@dataclass
class CreateAgentResponse:
    """Response from creating an agent."""

    agent: Agent


class CreateAgentUseCase:
    """Use case for creating a new agent."""

    def __init__(self, agent_repo: IAgentRepository):
        """
        Initialize use case.

        Parameters
        ----------
        agent_repo : IAgentRepository
            Agent repository for persistence.
        """
        self.agent_repo = agent_repo

    async def execute(self, request: CreateAgentRequest) -> CreateAgentResponse:
        """
        Execute the create agent use case.

        Parameters
        ----------
        request : CreateAgentRequest
            The create request.

        Returns
        -------
        CreateAgentResponse
            The created agent.

        Raises
        ------
        ValueError
            If validation fails or agent already exists.
        """
        # Validate request
        if not request.id or not request.id.strip():
            raise ValueError("Agent ID is required")

        if not request.name or not request.name.strip():
            raise ValueError("Agent name is required")

        if not request.domain_id or not request.domain_id.strip():
            raise ValueError("Domain ID is required")

        if not request.system_prompt or not request.system_prompt.strip():
            raise ValueError("System prompt is required")

        if not request.capabilities:
            raise ValueError("Agent must have at least one capability")

        if request.temperature < 0 or request.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")

        if request.max_tokens < 1:
            raise ValueError("Max tokens must be at least 1")

        # Check if agent already exists
        existing = await self.agent_repo.find_by_id(request.id)
        if existing:
            raise ValueError(f"Agent with ID '{request.id}' already exists")

        existing_name = await self.agent_repo.find_by_name(request.name)
        if existing_name:
            raise ValueError(f"Agent with name '{request.name}' already exists")

        # Create agent in development state
        agent = Agent(
            id=request.id,
            name=request.name,
            domain_id=request.domain_id,
            description=request.description,
            version=SemanticVersion(0, 1, 0),  # Start at 0.1.0
            state=AgentState.DEVELOPMENT,  # New agents start in development
            system_prompt=request.system_prompt,
            capabilities=request.capabilities,
            tools=request.tools,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout_seconds=request.timeout_seconds,
            keywords=request.keywords or [],
            priority=request.priority,
            author=request.author,
        )

        # Persist
        saved_agent = await self.agent_repo.save(agent)

        return CreateAgentResponse(agent=saved_agent)
