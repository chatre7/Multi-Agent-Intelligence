"""TDD tests for fine-grained permissions enforcement."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_user_cannot_execute_tools_without_execute_permission() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer;user:userpass:user"

    client = TestClient(create_app())
    user_token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    user_headers = {"authorization": f"Bearer {user_token}"}

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={"tool_id": "echo", "parameters": {"value": "hi"}},
    )
    assert created.status_code == 200
    run_id = created.json()["id"]
    assert created.json()["status"] == "approved"

    denied = client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=user_headers,
        json={},
    )
    assert denied.status_code == 403


def test_developer_can_execute_tools() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer;user:userpass:user"

    client = TestClient(create_app())
    developer_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    developer_headers = {"authorization": f"Bearer {developer_token}"}

    created = client.post(
        "/v1/tool-runs",
        headers=developer_headers,
        json={"tool_id": "echo", "parameters": {"value": "hi"}},
    )
    assert created.status_code == 200
    run_id = created.json()["id"]

    executed = client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=developer_headers,
        json={},
    )
    assert executed.status_code == 200
    assert executed.json()["status"] == "executed"
