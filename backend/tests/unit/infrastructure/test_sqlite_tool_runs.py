"""TDD tests for SQLite ToolRun repository adapter.

Note: use a workspace-local temp directory (sandbox-safe).
"""

from __future__ import annotations

from uuid import uuid4

from src.domain.entities.tool_run import ToolRun
from src.domain.value_objects.tool_run_status import ToolRunStatus


def test_sqlite_tool_run_repository_roundtrip() -> None:
    from src.infrastructure.persistence.sqlite.tool_runs import SqliteToolRunRepository

    db_uri = f"file:tool_runs_{uuid4()}?mode=memory&cache=shared"
    repo = SqliteToolRunRepository(db_path=db_uri)

    run_id = str(uuid4())
    tool_run = ToolRun(
        id=run_id,
        tool_id="save_file",
        parameters={"path": "x.txt", "content": "hello"},
        requested_by_role="user",
        requested_by_sub="alice",
        requires_approval=True,
        status=ToolRunStatus.PENDING_APPROVAL,
    )
    repo.add(tool_run)

    loaded = repo.get(run_id)
    assert loaded is not None
    assert loaded.id == run_id
    assert loaded.tool_id == "save_file"
    assert loaded.parameters["path"] == "x.txt"
    assert loaded.status == ToolRunStatus.PENDING_APPROVAL
    assert loaded.requested_by_sub == "alice"

    loaded.approve("admin")
    repo.update(loaded)

    loaded2 = repo.get(run_id)
    assert loaded2 is not None
    assert loaded2.status == ToolRunStatus.APPROVED
    assert loaded2.approved_at is not None


def test_sqlite_tool_run_repository_filters_and_cursor() -> None:
    from src.infrastructure.persistence.sqlite.tool_runs import SqliteToolRunRepository

    db_uri = f"file:tool_runs_{uuid4()}?mode=memory&cache=shared"
    repo = SqliteToolRunRepository(db_path=db_uri)

    pending = ToolRun(
        id=str(uuid4()),
        tool_id="save_file",
        parameters={"path": "a.txt", "content": "a"},
        requested_by_role="user",
        requested_by_sub="alice",
        requires_approval=True,
        status=ToolRunStatus.PENDING_APPROVAL,
    )
    executed = ToolRun(
        id=str(uuid4()),
        tool_id="save_file",
        parameters={"path": "b.txt", "content": "b"},
        requested_by_role="user",
        requested_by_sub="bob",
        requires_approval=True,
        status=ToolRunStatus.PENDING_APPROVAL,
    )
    executed.approve("admin")
    executed.mark_executed("admin", {"ok": True})

    repo.add(pending)
    repo.add(executed)

    only_executed = repo.list_recent(limit=10, status="executed")
    assert all(run.status == ToolRunStatus.EXECUTED for run in only_executed)

    alice_only = repo.list_recent(limit=10, requested_by_sub="alice")
    assert [run.id for run in alice_only] == [pending.id]

    page_1 = repo.list_recent(limit=1)
    assert len(page_1) == 1
    cursor = repo.get_next_cursor(page_1, has_more=True)
    assert cursor is not None

    page_2 = repo.list_recent(limit=1, cursor=cursor)
    assert len(page_2) == 1
    ids = {page_1[0].id, page_2[0].id}
    assert pending.id in ids
    assert executed.id in ids
