"""TDD tests for tool-run WebSocket events (MVP)."""

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


def test_websocket_tool_run_flow() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    admin_headers = {"authorization": f"Bearer {_token(client, 'admin', 'adminpass')}"}

    with client.websocket_connect("/ws", headers=user_headers) as ws:
        ws.send_json(
            {
                "type": "tool_run.request",
                "tool_id": "save_file",
                "parameters": {"path": "x.txt", "content": "hello"},
            }
        )
        created = ws.receive_json()
        assert created["type"] == "tool_run.created"
        run_id = created["run"]["id"]
        assert created["run"]["status"] == "pending_approval"
        assert created["run"]["requested_by_sub"] == "user"

    with client.websocket_connect("/ws", headers=admin_headers) as ws_admin:
        ws_admin.send_json({"type": "tool_run.approve", "run_id": run_id})
        approved = ws_admin.receive_json()
        assert approved["type"] == "tool_run.approved"
        assert approved["run"]["status"] == "approved"

        ws_admin.send_json({"type": "tool_run.execute", "run_id": run_id})
        executed = ws_admin.receive_json()
        assert executed["type"] == "tool_run.executed"
        assert executed["run"]["status"] == "executed"
        assert executed["run"]["result"]["ok"] is True


def test_websocket_tool_run_reject_blocks_execute() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    admin_headers = {"authorization": f"Bearer {_token(client, 'admin', 'adminpass')}"}

    with client.websocket_connect("/ws", headers=user_headers) as ws:
        ws.send_json(
            {
                "type": "tool_run.request",
                "tool_id": "save_file",
                "parameters": {"path": "x.txt", "content": "hello"},
            }
        )
        created = ws.receive_json()
        run_id = created["run"]["id"]

    with client.websocket_connect("/ws", headers=admin_headers) as ws_admin:
        ws_admin.send_json(
            {
                "type": "tool_run.reject",
                "run_id": run_id,
                "reason": "no",
            }
        )
        rejected = ws_admin.receive_json()
        assert rejected["type"] == "tool_run.rejected"
        assert rejected["run"]["status"] == "rejected"

        ws_admin.send_json({"type": "tool_run.execute", "run_id": run_id})
        denied = ws_admin.receive_json()
        assert denied["type"] == "error"


def test_websocket_tool_run_list_pagination() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    with client.websocket_connect("/ws", headers=user_headers) as ws:
        # Create two runs via WS so we don't depend on auth mode
        ws.send_json(
            {
                "type": "tool_run.request",
                "tool_id": "save_file",
                "parameters": {"path": "a.txt", "content": "a"},
            }
        )
        run_a = ws.receive_json()["run"]
        ws.send_json(
            {
                "type": "tool_run.request",
                "tool_id": "save_file",
                "parameters": {"path": "b.txt", "content": "b"},
            }
        )
        run_b = ws.receive_json()["run"]

    with client.websocket_connect("/ws", headers=dev_headers) as ws_dev:
        ws_dev.send_json({"type": "tool_run.list", "limit": 1})
        page_1 = ws_dev.receive_json()
        assert page_1["type"] == "tool_run.listed"
        assert isinstance(page_1["runs"], list)
        assert len(page_1["runs"]) == 1
        assert page_1.get("next_cursor") is not None

        ws_dev.send_json(
            {"type": "tool_run.list", "limit": 1, "cursor": page_1["next_cursor"]}
        )
        page_2 = ws_dev.receive_json()
        assert page_2["type"] == "tool_run.listed"
        assert isinstance(page_2["runs"], list)
        assert len(page_2["runs"]) == 1

        ids = {page_1["runs"][0]["id"], page_2["runs"][0]["id"]}
        assert run_a["id"] in ids
        assert run_b["id"] in ids


def test_websocket_tool_run_list_invalid_cursor_errors() -> None:
    client = _jwt_client()
    dev_headers = {
        "authorization": f"Bearer {_token(client, 'developer', 'developerpass')}"
    }

    with client.websocket_connect("/ws", headers=dev_headers) as ws:
        ws.send_json({"type": "tool_run.list", "limit": 10, "cursor": "bad"})
        error = ws.receive_json()
        assert error["type"] == "error"
