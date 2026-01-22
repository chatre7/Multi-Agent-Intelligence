"""Request tool run use case (MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from src.domain.entities.tool_run import ToolRun
from src.domain.repositories.tool_run_repository import IToolRunRepository
from src.domain.value_objects.tool_run_status import ToolRunStatus
from src.infrastructure.auth import Permission, require_permission_set
from src.infrastructure.config import YamlConfigLoader


@dataclass(frozen=True)
class RequestToolRunRequest:
    tool_id: str
    parameters: dict
    requested_by_role: str
    requested_by_permissions: frozenset[Permission]
    requested_by_subject: str = ""
    conversation_id: str = ""


@dataclass(frozen=True)
class RequestToolRunResponse:
    run_id: str
    tool_id: str
    requires_approval: bool
    status: str


@dataclass
class RequestToolRunUseCase:
    loader: YamlConfigLoader
    repo: IToolRunRepository

    def execute(self, request: RequestToolRunRequest) -> RequestToolRunResponse:
        require_permission_set(
            request.requested_by_permissions, Permission.TOOL_REQUEST
        )
        bundle = self.loader.load_bundle()
        tool = bundle.tools.get(request.tool_id)
        if tool is None:
            raise ValueError(f"Unknown tool_id: {request.tool_id}")

        is_valid, errors = tool.validate_parameters(request.parameters)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {errors}")

        run_id = str(uuid4())
        requires_approval = bool(tool.requires_approval)

        tool_run = ToolRun(
            id=run_id,
            tool_id=tool.id,
            parameters=dict(request.parameters),
            requested_by_role=request.requested_by_role,
            requested_by_sub=request.requested_by_subject,
            conversation_id=request.conversation_id,
            requires_approval=requires_approval,
            status=ToolRunStatus.PENDING_APPROVAL
            if requires_approval
            else ToolRunStatus.APPROVED,
            approved_by_role=None if requires_approval else "system",
        )
        self.repo.add(tool_run)
        return RequestToolRunResponse(
            run_id=tool_run.id,
            tool_id=tool_run.tool_id,
            requires_approval=tool_run.requires_approval,
            status=tool_run.status.value,
        )
