"""Create Domain Use Case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.entities.domain_config import DomainConfig, RoutingRule
from src.domain.repositories.domain_repository import IDomainRepository


@dataclass
class CreateDomainRequest:
    """Request to create a new domain."""

    id: str
    name: str
    description: str
    agents: list[str]
    default_agent: str
    workflow_type: str = "supervisor"
    max_iterations: int = 10
    fallback_agent: Optional[str] = None
    allowed_roles: Optional[list[str]] = None


@dataclass
class CreateDomainResponse:
    """Response from creating a domain."""

    domain: DomainConfig


class CreateDomainUseCase:
    """Use case for creating a new domain."""

    def __init__(self, domain_repo: IDomainRepository):
        self.domain_repo = domain_repo

    async def execute(self, request: CreateDomainRequest) -> CreateDomainResponse:
        """Execute create domain."""
        # Validate
        if not request.id or not request.id.strip():
            raise ValueError("Domain ID is required")

        if not request.name or not request.name.strip():
            raise ValueError("Domain name is required")

        if not request.agents:
            raise ValueError("Domain must have at least one agent")

        if request.default_agent not in request.agents:
            raise ValueError("Default agent must be in agents list")

        if request.workflow_type not in {
            "supervisor",
            "sequential",
            "parallel",
            "consensus",
        }:
            raise ValueError(f"Invalid workflow type: {request.workflow_type}")

        # Check if exists
        existing = await self.domain_repo.find_by_id(request.id)
        if existing:
            raise ValueError(f"Domain '{request.id}' already exists")

        # Create domain
        domain = DomainConfig(
            id=request.id,
            name=request.name,
            description=request.description,
            agents=request.agents,
            default_agent=request.default_agent,
            workflow_type=request.workflow_type,
            max_iterations=request.max_iterations,
            fallback_agent=request.fallback_agent or request.default_agent,
            allowed_roles=request.allowed_roles or ["user", "developer", "admin"],
        )

        # Validate
        errors = domain.validate()
        if errors:
            raise ValueError(f"Domain validation failed: {', '.join(errors)}")

        # Save
        saved = await self.domain_repo.save(domain)
        return CreateDomainResponse(domain=saved)
