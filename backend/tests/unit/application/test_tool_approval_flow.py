"""TDD tests for tool approval workflow (MVP)."""

from __future__ import annotations

import pytest


def test_request_tool_run_requires_approval() -> None:
    """Requesting a tool that requires approval creates a PENDING run."""
    from src.application.use_cases.tools import (
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()
    use_case = RequestToolRunUseCase(loader=loader, repo=repo)

    response = use_case.execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    assert response.tool_id == "save_file"
    assert response.status == "pending_approval"
    assert response.requires_approval is True


def test_execute_denied_before_approval() -> None:
    """Execution is blocked until approved."""
    from src.application.use_cases.tools import (
        ExecuteToolRunRequest,
        ExecuteToolRunUseCase,
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()

    request_uc = RequestToolRunUseCase(loader=loader, repo=repo)
    execute_uc = ExecuteToolRunUseCase(loader=loader, repo=repo)

    created = request_uc.execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    with pytest.raises(PermissionError):
        execute_uc.execute(
            ExecuteToolRunRequest(
                run_id=created.run_id,
                executed_by_role="admin",
                executed_by_permissions=permissions_for_role("admin"),
            )
        )


def test_approve_then_execute_succeeds() -> None:
    """Admin approves then executes; handler runs and result is stored."""
    from src.application.use_cases.tools import (
        ApproveToolRunRequest,
        ApproveToolRunUseCase,
        ExecuteToolRunRequest,
        ExecuteToolRunUseCase,
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()

    request_uc = RequestToolRunUseCase(loader=loader, repo=repo)
    approve_uc = ApproveToolRunUseCase(loader=loader, repo=repo)
    execute_uc = ExecuteToolRunUseCase(loader=loader, repo=repo)

    created = request_uc.execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    approved = approve_uc.execute(
        ApproveToolRunRequest(
            run_id=created.run_id,
            approved_by_role="admin",
            approved_by_permissions=permissions_for_role("admin"),
        )
    )
    assert approved.status == "approved"

    executed = execute_uc.execute(
        ExecuteToolRunRequest(
            run_id=created.run_id,
            executed_by_role="admin",
            executed_by_permissions=permissions_for_role("admin"),
        )
    )
    assert executed.status == "executed"
    assert executed.result.get("ok") is True


def test_non_admin_cannot_approve() -> None:
    """Only developer/admin can approve tools in this MVP."""
    from src.application.use_cases.tools import (
        ApproveToolRunRequest,
        ApproveToolRunUseCase,
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()

    created = RequestToolRunUseCase(loader=loader, repo=repo).execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    approve_uc = ApproveToolRunUseCase(loader=loader, repo=repo)
    with pytest.raises(PermissionError):
        approve_uc.execute(
            ApproveToolRunRequest(
                run_id=created.run_id,
                approved_by_role="user",
                approved_by_permissions=permissions_for_role("user"),
            )
        )


def test_reject_then_execute_denied() -> None:
    """After rejection, execution is denied."""
    from src.application.use_cases.tools import (
        ExecuteToolRunRequest,
        ExecuteToolRunUseCase,
        RejectToolRunRequest,
        RejectToolRunUseCase,
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()

    request_uc = RequestToolRunUseCase(loader=loader, repo=repo)
    reject_uc = RejectToolRunUseCase(loader=loader, repo=repo)
    execute_uc = ExecuteToolRunUseCase(loader=loader, repo=repo)

    created = request_uc.execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    rejected = reject_uc.execute(
        RejectToolRunRequest(
            run_id=created.run_id,
            rejected_by_role="admin",
            rejected_by_permissions=permissions_for_role("admin"),
            reason="Not allowed right now",
        )
    )
    assert rejected.status == "rejected"

    with pytest.raises(PermissionError):
        execute_uc.execute(
            ExecuteToolRunRequest(
                run_id=created.run_id,
                executed_by_role="admin",
                executed_by_permissions=permissions_for_role("admin"),
            )
        )


def test_non_admin_cannot_reject() -> None:
    """Only developer/admin can reject in this MVP."""
    from src.application.use_cases.tools import (
        RejectToolRunRequest,
        RejectToolRunUseCase,
        RequestToolRunRequest,
        RequestToolRunUseCase,
    )
    from src.infrastructure.auth import permissions_for_role
    from src.infrastructure.config import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.tool_runs import (
        InMemoryToolRunRepository,
    )

    repo = InMemoryToolRunRepository()
    loader = YamlConfigLoader.from_default_backend_root()

    created = RequestToolRunUseCase(loader=loader, repo=repo).execute(
        RequestToolRunRequest(
            tool_id="save_file",
            parameters={"path": "x.txt", "content": "hello"},
            requested_by_role="user",
            requested_by_permissions=permissions_for_role("user"),
        )
    )

    reject_uc = RejectToolRunUseCase(loader=loader, repo=repo)
    with pytest.raises(PermissionError):
        reject_uc.execute(
            RejectToolRunRequest(
                run_id=created.run_id,
                rejected_by_role="user",
                rejected_by_permissions=permissions_for_role("user"),
                reason="nope",
            )
        )
