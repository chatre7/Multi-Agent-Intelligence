"""List Domains Use Case."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.domain_config import DomainConfig
from src.domain.repositories.domain_repository import IDomainRepository


@dataclass
class ListDomainsRequest:
    """Request to list domains."""

    active_only: bool = False


@dataclass
class ListDomainsResponse:
    """Response from listing domains."""

    domains: list[DomainConfig]
    count: int


class ListDomainsUseCase:
    """Use case for listing domains."""

    def __init__(self, domain_repo: IDomainRepository):
        self.domain_repo = domain_repo

    async def execute(self, request: ListDomainsRequest) -> ListDomainsResponse:
        """Execute list domains."""
        if request.active_only:
            domains = await self.domain_repo.find_active()
        else:
            domains = await self.domain_repo.find_all()

        return ListDomainsResponse(domains=domains, count=len(domains))
