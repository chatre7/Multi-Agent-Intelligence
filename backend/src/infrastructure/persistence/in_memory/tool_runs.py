"""In-memory ToolRun repository (MVP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from src.domain.entities.tool_run import ToolRun
from src.domain.repositories.tool_run_repository import IToolRunRepository


def _cursor_for(run: ToolRun) -> str:
    return f"{run.updated_at.isoformat()}|{run.id}"


@dataclass
class InMemoryToolRunRepository(IToolRunRepository):
    """Thread-safe in-memory storage for tool runs."""

    _by_id: dict[str, ToolRun] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def add(self, tool_run: ToolRun) -> None:
        with self._lock:
            self._by_id[tool_run.id] = tool_run

    def get(self, run_id: str) -> ToolRun | None:
        with self._lock:
            return self._by_id.get(run_id)

    def update(self, tool_run: ToolRun) -> None:
        with self._lock:
            if tool_run.id not in self._by_id:
                raise KeyError(f"Unknown tool run id: {tool_run.id}")
            self._by_id[tool_run.id] = tool_run

    def _list_recent_filtered(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        tool_id: str | None = None,
        requested_by_sub: str | None = None,
        cursor: str | None = None,
    ) -> list[ToolRun]:
        with self._lock:
            runs = list(self._by_id.values())

        if status is not None:
            status_lower = status.lower()
            runs = [run for run in runs if run.status.value == status_lower]
        if tool_id is not None:
            runs = [run for run in runs if run.tool_id == tool_id]
        if requested_by_sub is not None:
            runs = [run for run in runs if run.requested_by_sub == requested_by_sub]

        runs.sort(
            key=lambda run: run.updated_at
            if isinstance(run.updated_at, datetime)
            else run.created_at,
            reverse=True,
        )

        start_index = 0
        if cursor:
            for index, run in enumerate(runs):
                if _cursor_for(run) == cursor:
                    start_index = index + 1
                    break

        page = runs[start_index : start_index + int(limit)]
        return page

    def list_recent(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        tool_id: str | None = None,
        requested_by_sub: str | None = None,
        cursor: str | None = None,
    ) -> list[ToolRun]:
        return self._list_recent_filtered(
            limit=limit,
            status=status,
            tool_id=tool_id,
            requested_by_sub=requested_by_sub,
            cursor=cursor,
        )

    def get_next_cursor(self, runs: list[ToolRun], *, has_more: bool) -> str | None:
        if not has_more or not runs:
            return None
        return _cursor_for(runs[-1])
