"""Delete Domain Use Case."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.domain_repository import IDomainRepository


@dataclass
class DeleteDomainRequest:
    """Request to delete a domain."""

    domain_id: str


@dataclass
class DeleteDomainResponse:
    """Response from deleting a domain."""

    deleted: bool
    message: str


class DeleteDomainUseCase:
    """Use case for deleting a domain."""

    def __init__(self, domain_repo: IDomainRepository):
        self.domain_repo = domain_repo

    async def execute(self, request: DeleteDomainRequest) -> DeleteDomainResponse:
        """Execute delete domain."""
        domain = await self.domain_repo.find_by_id(request.domain_id)
        if not domain:
            raise ValueError(f"Domain '{request.domain_id}' not found")

        deleted = await self.domain_repo.delete(request.domain_id)

        return DeleteDomainResponse(
            deleted=deleted,
            message=f"Domain '{request.domain_id}' deleted"
            if deleted
            else "Failed to delete domain",
        )
