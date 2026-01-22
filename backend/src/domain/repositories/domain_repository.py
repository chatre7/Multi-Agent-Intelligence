"""Domain Repository Interface (Port)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.domain_config import DomainConfig


class IDomainRepository(ABC):
    """Port for DomainConfig persistence operations."""

    @abstractmethod
    async def save(self, domain: DomainConfig) -> DomainConfig:
        """Persist a domain (create or update)."""
        pass

    @abstractmethod
    async def find_by_id(self, domain_id: str) -> Optional[DomainConfig]:
        """Find domain by ID."""
        pass

    @abstractmethod
    async def find_all(self) -> List[DomainConfig]:
        """Get all domains."""
        pass

    @abstractmethod
    async def delete(self, domain_id: str) -> bool:
        """Delete a domain by ID."""
        pass

    @abstractmethod
    async def find_active(self) -> List[DomainConfig]:
        """Get all active domains."""
        pass

    @abstractmethod
    async def exists(self, domain_id: str) -> bool:
        """Check if domain exists."""
        pass
