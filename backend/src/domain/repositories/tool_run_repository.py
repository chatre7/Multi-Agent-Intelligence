"""Repository interface for tool runs."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.tool_run import ToolRun


class IToolRunRepository(ABC):
    """Port for storing and retrieving ToolRun entities."""

    @abstractmethod
    def add(self, tool_run: ToolRun) -> None:
        """Persist a tool run."""

    @abstractmethod
    def get(self, run_id: str) -> ToolRun | None:
        """Fetch a tool run by id."""

    @abstractmethod
    def update(self, tool_run: ToolRun) -> None:
        """Update an existing tool run."""

    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        tool_id: str | None = None,
        requested_by_sub: str | None = None,
        cursor: str | None = None,
    ) -> list[ToolRun]:
        """List most recent tool runs with optional filters and cursor."""

    @abstractmethod
    def get_next_cursor(self, runs: list[ToolRun], *, has_more: bool) -> str | None:
        """Return a cursor for the next page if available."""
