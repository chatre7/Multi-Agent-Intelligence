"""TDD tests for ToolRun audit timestamps."""

from __future__ import annotations

from src.domain.entities.tool_run import ToolRun
from src.domain.value_objects.tool_run_status import ToolRunStatus


def test_tool_run_timestamps_set_on_actions() -> None:
    run = ToolRun(
        id="run-1",
        tool_id="save_file",
        parameters={"path": "x", "content": "y"},
        requested_by_role="user",
        requires_approval=True,
    )
    assert run.approved_at is None
    assert run.rejected_at is None
    assert run.executed_at is None

    run.approve("admin")
    assert run.status == ToolRunStatus.APPROVED
    assert run.approved_at is not None

    run.mark_executed("admin", {"ok": True})
    assert run.status == ToolRunStatus.EXECUTED
    assert run.executed_at is not None
