"""Repository interface for long-term memory (facts)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IMemoryRepository(ABC):
    """Port for persisting and searching long-term memory (facts)."""

    @abstractmethod
    def add_memories(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None, 
        ids: Optional[List[str]] = None
    ) -> None:
        """Add new memories to the store."""

    @abstractmethod
    def search_memories(
        self, 
        query: str, 
        limit: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories based on a query."""

    @abstractmethod
    def delete_memories(self, ids: List[str]) -> None:
        """Delete specific memories by ID."""

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all memories for the current collection."""
