"""TDD tests for permission enforcement on read/admin endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _jwt_client() -> TestClient:
    import os

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "admin:adminpass:admin;developer:developerpass:developer;user:userpass:user"
    )
    from src.presentation.api.app import create_app

    return TestClient(create_app())


def _token(client: TestClient, username: str, password: str) -> str:
    resp = client.post(
        "/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_metrics_requires_metrics_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    denied = client.get("/metrics", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get("/metrics", headers=dev_headers)
    assert ok.status_code == 200


def test_health_details_requires_health_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    denied = client.get("/health/details", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get("/health/details", headers=dev_headers)
    assert ok.status_code == 200


def test_tool_run_list_requires_tool_read_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    denied = client.get("/v1/tool-runs?limit=10", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get("/v1/tool-runs?limit=10", headers=dev_headers)
    assert ok.status_code == 200


def test_tool_run_get_requires_tool_read_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }
    admin_headers = {"authorization": f"Bearer {_token(client, 'admin', 'adminpass')}"}

    created = client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    run_id = created.json()["id"]

    denied = client.get(f"/v1/tool-runs/{run_id}", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get(f"/v1/tool-runs/{run_id}", headers=dev_headers)
    assert ok.status_code == 200
    assert ok.json()["id"] == run_id

    ok2 = client.get(f"/v1/tool-runs/{run_id}", headers=admin_headers)
    assert ok2.status_code == 200


def test_tools_list_requires_tool_read_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    denied = client.get("/v1/tools", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get("/v1/tools", headers=dev_headers)
    assert ok.status_code == 200
    assert isinstance(ok.json(), list)


def test_agents_list_requires_agent_read_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    denied = client.get("/v1/agents", headers=user_headers)
    assert denied.status_code == 403

    ok = client.get("/v1/agents", headers=dev_headers)
    assert ok.status_code == 200
    assert isinstance(ok.json(), list)


def test_conversation_messages_requires_chat_read_permission() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}

    chat = client.post(
        "/v1/chat",
        headers=user_headers,
        json={"domain_id": "software_development", "message": "hello"},
    )
    conversation_id = chat.json()["conversation_id"]

    denied = client.get(f"/v1/conversations/{conversation_id}/messages")
    assert denied.status_code == 401

    ok = client.get(
        f"/v1/conversations/{conversation_id}/messages", headers=user_headers
    )
    assert ok.status_code == 200
