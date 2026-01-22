"""Execute tool run use case (MVP)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.tool_run_repository import IToolRunRepository
from src.domain.value_objects.tool_run_status import ToolRunStatus
from src.infrastructure.auth import Permission, require_permission_set
from src.infrastructure.config import YamlConfigLoader

from ._shared import load_handler, normalize_result


@dataclass(frozen=True)
class ExecuteToolRunRequest:
    run_id: str
    executed_by_role: str
    executed_by_permissions: frozenset[Permission]


@dataclass(frozen=True)
class ExecuteToolRunResponse:
    run_id: str
    status: str
    result: dict


@dataclass
class ExecuteToolRunUseCase:
    loader: YamlConfigLoader
    repo: IToolRunRepository

    def execute(self, request: ExecuteToolRunRequest) -> ExecuteToolRunResponse:
        tool_run = self.repo.get(request.run_id)
        if tool_run is None:
            raise ValueError("Unknown run_id")

        bundle = self.loader.load_bundle()
        tool = bundle.tools.get(tool_run.tool_id)
        if tool is None:
            raise ValueError("Unknown tool_id for tool run")

        role = request.executed_by_role.lower()
        require_permission_set(request.executed_by_permissions, Permission.TOOL_EXECUTE)
        if not tool.is_role_allowed(role):
            raise PermissionError("Role not allowed to execute this tool.")

        if tool_run.requires_approval and tool_run.status != ToolRunStatus.APPROVED:
            raise PermissionError("Tool run not approved.")
        if tool_run.status == ToolRunStatus.REJECTED:
            raise PermissionError("Tool run rejected.")
        if tool_run.status == ToolRunStatus.EXECUTED:
            return ExecuteToolRunResponse(
                run_id=tool_run.id,
                status=tool_run.status.value,
                result=dict(tool_run.result),
            )

        is_valid, errors = tool.validate_parameters(tool_run.parameters)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {errors}")

        handler = load_handler(tool.handler_path)
        try:
            raw_result = handler(**tool_run.parameters)
            result = normalize_result(raw_result)
            tool_run.mark_executed(role, result)
        except Exception as exc:  # noqa: BLE001
            tool_run.mark_failed(role, str(exc))
        self.repo.update(tool_run)

        return ExecuteToolRunResponse(
            run_id=tool_run.id,
            status=tool_run.status.value,
            result=dict(tool_run.result),
        )
