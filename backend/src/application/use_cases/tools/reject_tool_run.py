"""Reject tool run use case (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.tool_run_repository import IToolRunRepository
from src.infrastructure.auth import Permission, require_permission_set
from src.infrastructure.config import YamlConfigLoader


@dataclass(frozen=True)
class RejectToolRunRequest:
    run_id: str
    rejected_by_role: str
    rejected_by_permissions: frozenset[Permission]
    reason: str


@dataclass(frozen=True)
class RejectToolRunResponse:
    run_id: str
    status: str


@dataclass
class RejectToolRunUseCase:
    loader: YamlConfigLoader
    repo: IToolRunRepository

    def execute(self, request: RejectToolRunRequest) -> RejectToolRunResponse:
        role = request.rejected_by_role.lower()
        require_permission_set(request.rejected_by_permissions, Permission.TOOL_REJECT)
        if not request.reason.strip():
            raise ValueError("Rejection reason is required.")

        tool_run = self.repo.get(request.run_id)
        if tool_run is None:
            raise ValueError("Unknown run_id")

        bundle = self.loader.load_bundle()
        tool = bundle.tools.get(tool_run.tool_id)
        if tool is None:
            raise ValueError("Unknown tool_id for tool run")
        if not tool.requires_approval:
            raise ValueError("This tool does not require approval.")

        tool_run.reject(role, request.reason.strip())
        self.repo.update(tool_run)
        return RejectToolRunResponse(run_id=tool_run.id, status=tool_run.status.value)
