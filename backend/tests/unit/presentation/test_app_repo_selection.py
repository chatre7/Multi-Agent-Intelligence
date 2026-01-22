"""TDD tests for tool-run repository selection in create_app()."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_app_defaults_to_in_memory_repo(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    monkeypatch.delenv("TOOL_RUN_REPO", raising=False)
    monkeypatch.delenv("TOOL_RUN_DB", raising=False)
    monkeypatch.setenv("AUTH_MODE", "header")

    client = TestClient(create_app())
    created = client.post(
        "/v1/tool-runs",
        headers={"x-role": "user"},
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert created.status_code == 200


def test_create_app_can_use_sqlite_repo_via_env(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    db_uri = f"file:tool_runs_app_{uuid4()}?mode=memory&cache=shared"
    monkeypatch.setenv("AUTH_MODE", "header")
    monkeypatch.setenv("TOOL_RUN_REPO", "sqlite")
    monkeypatch.setenv("TOOL_RUN_DB", db_uri)

    client = TestClient(create_app())
    created = client.post(
        "/v1/tool-runs",
        headers={"x-role": "user"},
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert created.status_code == 200
    run_id = created.json()["id"]

    # New app instance should see the same DB (shared memory)
    client2 = TestClient(create_app())
    loaded = client2.get(f"/v1/tool-runs/{run_id}", headers={"x-role": "developer"})
    assert loaded.status_code == 200
    assert loaded.json()["id"] == run_id
