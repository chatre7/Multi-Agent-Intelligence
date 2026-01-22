"""TDD tests for tool run REST endpoints (MVP)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers_for(client: TestClient, role: str) -> dict:
    login = client.post(
        "/v1/auth/login",
        json={"username": role, "password": f"{role}pass"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"authorization": f"Bearer {token}"}


def _jwt_client() -> TestClient:
    import os

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "admin:adminpass:admin;developer:developerpass:developer;user:userpass:user"
    )
    from src.presentation.api.app import create_app

    return TestClient(create_app())


def test_tool_run_endpoints_happy_path() -> None:
    client = _jwt_client()
    user_headers = _auth_headers_for(client, "user")
    admin_headers = _auth_headers_for(client, "admin")

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert created.status_code == 200
    run_id = created.json()["id"]
    assert created.json()["status"] == "pending_approval"

    approved = client.post(
        f"/v1/tool-runs/{run_id}/approve",
        headers=admin_headers,
        json={},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    executed = client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=admin_headers,
        json={},
    )
    assert executed.status_code == 200
    assert executed.json()["status"] == "executed"
    assert executed.json()["result"]["ok"] is True


def test_tool_run_execute_denied_for_user_role() -> None:
    client = _jwt_client()
    user_headers = _auth_headers_for(client, "user")

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    run_id = created.json()["id"]

    denied = client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=user_headers,
        json={},
    )
    assert denied.status_code == 403


def test_tool_run_reject_endpoint() -> None:
    client = _jwt_client()
    user_headers = _auth_headers_for(client, "user")
    admin_headers = _auth_headers_for(client, "admin")

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    run_id = created.json()["id"]

    rejected = client.post(
        f"/v1/tool-runs/{run_id}/reject",
        headers=admin_headers,
        json={"reason": "no"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    executed = client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=admin_headers,
        json={},
    )
    assert executed.status_code == 403
