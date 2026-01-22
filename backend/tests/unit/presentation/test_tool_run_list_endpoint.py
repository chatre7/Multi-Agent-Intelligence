"""TDD tests for listing tool runs (MVP)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_tool_runs_returns_recent_runs() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "admin:adminpass:admin;developer:developerpass:developer;user:userpass:user"
    )

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    user_headers = {"authorization": f"Bearer {token}"}
    admin_token = client.post(
        "/v1/auth/login", json={"username": "admin", "password": "adminpass"}
    ).json()["access_token"]
    admin_headers = {"authorization": f"Bearer {admin_token}"}
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    run_id = created.json()["id"]

    client.post(
        f"/v1/tool-runs/{run_id}/approve",
        headers=admin_headers,
        json={},
    )

    client.post(
        f"/v1/tool-runs/{run_id}/execute",
        headers=admin_headers,
        json={},
    )

    listed = client.get("/v1/tool-runs?limit=10", headers=dev_headers)
    assert listed.status_code == 200
    items = listed.json()
    assert isinstance(items, list)
    assert any(item["id"] == run_id for item in items)

    found = next(item for item in items if item["id"] == run_id)
    assert found["approved_at"] is not None
    assert found["executed_at"] is not None


def test_list_tool_runs_filters_and_cursor_pagination() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "admin:adminpass:admin;developer:developerpass:developer;user:userpass:user"
    )

    client = TestClient(create_app())
    user_token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    user_headers = {"authorization": f"Bearer {user_token}"}
    admin_token = client.post(
        "/v1/auth/login", json={"username": "admin", "password": "adminpass"}
    ).json()["access_token"]
    admin_headers = {"authorization": f"Bearer {admin_token}"}
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    created_1 = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={"tool_id": "save_file", "parameters": {"path": "a.txt", "content": "a"}},
    ).json()
    created_2 = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={"tool_id": "save_file", "parameters": {"path": "b.txt", "content": "b"}},
    ).json()

    # Approve + execute only the second run so we can filter by status
    client.post(
        f"/v1/tool-runs/{created_2['id']}/approve", headers=admin_headers, json={}
    )
    client.post(
        f"/v1/tool-runs/{created_2['id']}/execute", headers=admin_headers, json={}
    )

    executed_only = client.get(
        "/v1/tool-runs?status=executed&limit=10", headers=dev_headers
    )
    assert executed_only.status_code == 200
    items = executed_only.json()
    assert all(item["status"] == "executed" for item in items)
    assert any(item["id"] == created_2["id"] for item in items)
    assert not any(item["id"] == created_1["id"] for item in items)

    # Cursor pagination returns list body, with next cursor in header
    page_1 = client.get("/v1/tool-runs?limit=1", headers=dev_headers)
    assert page_1.status_code == 200
    assert isinstance(page_1.json(), list)
    assert len(page_1.json()) == 1
    cursor = page_1.headers.get("x-next-cursor")
    assert cursor is not None

    page_2 = client.get(f"/v1/tool-runs?limit=1&cursor={cursor}", headers=dev_headers)
    assert page_2.status_code == 200
    assert isinstance(page_2.json(), list)
    assert len(page_2.json()) == 1


def test_list_tool_runs_invalid_cursor_returns_400() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "admin:adminpass:admin;developer:developerpass:developer;user:userpass:user"
    )

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    user_headers = {"authorization": f"Bearer {token}"}
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert created.status_code == 200

    bad = client.get(
        "/v1/tool-runs?limit=10&cursor=not-a-valid-cursor", headers=dev_headers
    )
    assert bad.status_code == 400
