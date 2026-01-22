"""Approve tool run use case (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.tool_run_repository import IToolRunRepository
from src.infrastructure.auth import Permission, require_permission_set
from src.infrastructure.config import YamlConfigLoader


@dataclass(frozen=True)
class ApproveToolRunRequest:
    run_id: str
    approved_by_role: str
    approved_by_permissions: frozenset[Permission]


@dataclass(frozen=True)
class ApproveToolRunResponse:
    run_id: str
    status: str


@dataclass
class ApproveToolRunUseCase:
    loader: YamlConfigLoader
    repo: IToolRunRepository

    def execute(self, request: ApproveToolRunRequest) -> ApproveToolRunResponse:
        role = request.approved_by_role.lower()
        require_permission_set(request.approved_by_permissions, Permission.TOOL_APPROVE)

        tool_run = self.repo.get(request.run_id)
        if tool_run is None:
            raise ValueError("Unknown run_id")

        bundle = self.loader.load_bundle()
        tool = bundle.tools.get(tool_run.tool_id)
        if tool is None:
            raise ValueError("Unknown tool_id for tool run")
        if not tool.requires_approval:
            raise ValueError("This tool does not require approval.")

        tool_run.approve(role)
        self.repo.update(tool_run)
        return ApproveToolRunResponse(run_id=tool_run.id, status=tool_run.status.value)
