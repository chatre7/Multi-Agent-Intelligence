"""List tool runs use case (MVP)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.entities.tool_run import ToolRun
from src.domain.repositories.tool_run_repository import IToolRunRepository

_CURSOR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T.+\|[0-9a-fA-F-]{8,}$")


@dataclass(frozen=True)
class ListToolRunsRequest:
    limit: int = 50
    status: str | None = None
    tool_id: str | None = None
    requested_by_sub: str | None = None
    cursor: str | None = None


@dataclass(frozen=True)
class ListToolRunsResponse:
    runs: list[ToolRun]
    next_cursor: str | None


@dataclass
class ListToolRunsUseCase:
    repo: IToolRunRepository

    def execute(self, request: ListToolRunsRequest) -> ListToolRunsResponse:
        if request.cursor is not None and not _CURSOR_PATTERN.match(request.cursor):
            raise ValueError("Invalid cursor format.")

        limit = int(request.limit)
        if limit < 1:
            limit = 1
        if limit > 200:
            limit = 200
        fetched = self.repo.list_recent(
            limit=limit + 1,
            status=request.status,
            tool_id=request.tool_id,
            requested_by_sub=request.requested_by_sub,
            cursor=request.cursor,
        )
        has_more = len(fetched) > limit
        runs = fetched[:limit]
        next_cursor = self.repo.get_next_cursor(runs, has_more=has_more)
        return ListToolRunsResponse(runs=runs, next_cursor=next_cursor)
