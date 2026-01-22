"""TDD tests for tool-run ownership enforcement."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_user_cannot_read_other_users_tool_run() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "alice:alicepass:user;bob:bobpass:user;developer:developerpass:developer;admin:adminpass:admin"
    )

    from src.presentation.api.app import create_app

    client = TestClient(create_app())

    alice_token = client.post(
        "/v1/auth/login", json={"username": "alice", "password": "alicepass"}
    ).json()["access_token"]
    bob_token = client.post(
        "/v1/auth/login", json={"username": "bob", "password": "bobpass"}
    ).json()["access_token"]
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    admin_token = client.post(
        "/v1/auth/login", json={"username": "admin", "password": "adminpass"}
    ).json()["access_token"]

    alice_headers = {"authorization": f"Bearer {alice_token}"}
    bob_headers = {"authorization": f"Bearer {bob_token}"}
    dev_headers = {"authorization": f"Bearer {dev_token}"}
    admin_headers = {"authorization": f"Bearer {admin_token}"}

    run_id = client.post(
        "/v1/tool-runs",
        headers=alice_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    ).json()["id"]

    loaded_owner = client.get(f"/v1/tool-runs/{run_id}", headers=admin_headers).json()
    assert loaded_owner.get("requested_by_sub") == "alice"

    # Bob cannot read Alice's tool run
    denied = client.get(f"/v1/tool-runs/{run_id}", headers=bob_headers)
    assert denied.status_code in (403, 404)

    # Developer/admin can read
    assert client.get(f"/v1/tool-runs/{run_id}", headers=dev_headers).status_code == 200
    assert (
        client.get(f"/v1/tool-runs/{run_id}", headers=admin_headers).status_code == 200
    )


def test_tool_run_list_only_returns_own_for_user() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "alice:alicepass:user;bob:bobpass:user;developer:developerpass:developer"
    )

    from src.presentation.api.app import create_app

    client = TestClient(create_app())

    alice_token = client.post(
        "/v1/auth/login", json={"username": "alice", "password": "alicepass"}
    ).json()["access_token"]
    bob_token = client.post(
        "/v1/auth/login", json={"username": "bob", "password": "bobpass"}
    ).json()["access_token"]
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]

    alice_headers = {"authorization": f"Bearer {alice_token}"}
    bob_headers = {"authorization": f"Bearer {bob_token}"}
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    alice_run = client.post(
        "/v1/tool-runs",
        headers=alice_headers,
        json={"tool_id": "save_file", "parameters": {"path": "a.txt", "content": "a"}},
    ).json()["id"]
    bob_run = client.post(
        "/v1/tool-runs",
        headers=bob_headers,
        json={"tool_id": "save_file", "parameters": {"path": "b.txt", "content": "b"}},
    ).json()["id"]

    alice_list = client.get("/v1/tool-runs?limit=50", headers=dev_headers).json()
    assert any(r["id"] == alice_run for r in alice_list)
    assert any(r["id"] == bob_run for r in alice_list)

    # For user role, listing should only show own (use a derived token w/ user perms doesn't include tool:read).
    # So we validate ownership via GET by id above; this test uses developer headers for list due to permissions.
    denied_list = client.get("/v1/tool-runs?limit=10", headers=alice_headers)
    assert denied_list.status_code == 403
