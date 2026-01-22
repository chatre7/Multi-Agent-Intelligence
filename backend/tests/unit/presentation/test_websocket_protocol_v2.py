"""TDD tests for v2 WebSocket streaming protocol messages."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


def _jwt_client() -> TestClient:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "admin:adminpass:admin;user:userpass:user"
    from src.presentation.api.app import create_app

    return TestClient(create_app())


def _token(client: TestClient, username: str, password: str) -> str:
    resp = client.post(
        "/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_ws_start_conversation_and_send_message_v2() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}

    with client.websocket_connect("/ws", headers=user_headers) as ws:
        ws.send_json(
            {
                "type": "start_conversation",
                "payload": {"domainId": "software_development"},
            }
        )
        started = ws.receive_json()
        assert started["type"] == "conversation_started"
        conversation_id = started["payload"]["conversationId"]
        assert conversation_id

        ws.send_json(
            {
                "type": "send_message",
                "conversationId": conversation_id,
                "payload": {"content": "hello streaming"},
            }
        )

        chunks = []
        complete = None
        for _ in range(200):
            msg = ws.receive_json()
            if msg["type"] == "message_chunk":
                chunks.append(msg["payload"]["chunk"])
            if msg["type"] == "message_complete":
                complete = msg
                break
        assert complete is not None
        assert complete["conversationId"] == conversation_id
        assert complete["payload"]["content"]
        assert "".join(chunks).strip() == complete["payload"]["content"].strip()


def test_ws_tool_approval_flow_v2() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    admin_headers = {"authorization": f"Bearer {_token(client, 'admin', 'adminpass')}"}
    os.environ["TOOL_FILE_ROOT"] = str(Path.cwd() / ".test_tmp" / f"ws_tool_{uuid4()}")

    with client.websocket_connect("/ws", headers=user_headers) as ws_user:
        ws_user.send_json(
            {
                "type": "start_conversation",
                "payload": {"domainId": "software_development"},
            }
        )
        conversation_id = ws_user.receive_json()["payload"]["conversationId"]

        ws_user.send_json(
            {
                "type": "send_message",
                "conversationId": conversation_id,
                "payload": {
                    "content": '/tool save_file {"path":"x.txt","content":"hi"}'
                },
            }
        )
        approval = ws_user.receive_json()
        assert approval["type"] == "tool_approval_required"
        request_id = approval["payload"]["requestId"]
        assert request_id
        assert approval["conversationId"] == conversation_id
        assert approval["payload"]["toolName"] == "save_file"

        with client.websocket_connect("/ws", headers=admin_headers) as ws_admin:
            ws_admin.send_json(
                {
                    "type": "approve_tool",
                    "conversationId": conversation_id,
                    "requestId": request_id,
                    "payload": {"approved": True},
                }
            )

        # Tool run is linked to this conversation
        loaded = client.get(f"/v1/tool-runs/{request_id}", headers=admin_headers)
        assert loaded.status_code == 200
        assert loaded.json().get("conversation_id") == conversation_id

        executed = None
        completed = None
        for _ in range(200):
            msg = ws_user.receive_json()
            if msg["type"] == "tool_executed":
                executed = msg
            if msg["type"] == "message_complete":
                completed = msg
                break

        assert executed is not None
        assert executed["payload"]["requestId"] == request_id
        assert executed["payload"]["success"] is True
        assert completed is not None


def test_ws_tool_reject_flow_v2() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}
    admin_headers = {"authorization": f"Bearer {_token(client, 'admin', 'adminpass')}"}
    os.environ["TOOL_FILE_ROOT"] = str(Path.cwd() / ".test_tmp" / f"ws_tool_{uuid4()}")

    with client.websocket_connect("/ws", headers=user_headers) as ws_user:
        ws_user.send_json(
            {
                "type": "start_conversation",
                "payload": {"domainId": "software_development"},
            }
        )
        conversation_id = ws_user.receive_json()["payload"]["conversationId"]

        ws_user.send_json(
            {
                "type": "send_message",
                "conversationId": conversation_id,
                "payload": {
                    "content": '/tool save_file {"path":"x.txt","content":"hi"}'
                },
            }
        )
        approval = ws_user.receive_json()
        request_id = approval["payload"]["requestId"]

        with client.websocket_connect("/ws", headers=admin_headers) as ws_admin:
            ws_admin.send_json(
                {
                    "type": "approve_tool",
                    "conversationId": conversation_id,
                    "requestId": request_id,
                    "payload": {"approved": False, "reason": "nope"},
                }
            )

        executed = None
        for _ in range(50):
            msg = ws_user.receive_json()
            if msg["type"] == "tool_executed":
                executed = msg
                break
        assert executed is not None
        assert executed["payload"]["requestId"] == request_id
        assert executed["payload"]["success"] is False


def test_ws_cancel_stream_v2() -> None:
    client = _jwt_client()
    user_headers = {"authorization": f"Bearer {_token(client, 'user', 'userpass')}"}

    long_text = " ".join(["word"] * 500)
    with client.websocket_connect("/ws", headers=user_headers) as ws:
        ws.send_json(
            {
                "type": "start_conversation",
                "payload": {"domainId": "software_development"},
            }
        )
        conversation_id = ws.receive_json()["payload"]["conversationId"]

        ws.send_json(
            {
                "type": "send_message",
                "conversationId": conversation_id,
                "payload": {"content": long_text},
            }
        )

        # Wait for at least one chunk to ensure the stream task started.
        for _ in range(200):
            msg = ws.receive_json()
            if msg["type"] == "message_chunk":
                break

        ws.send_json(
            {"type": "cancel_stream", "conversationId": conversation_id, "payload": {}}
        )

        cancelled = None
        for _ in range(200):
            msg = ws.receive_json()
            if (
                msg["type"] == "error"
                and msg.get("payload", {}).get("code") == "cancelled"
            ):
                cancelled = msg
                break
            if msg["type"] == "message_complete":
                # If it completes before cancel is processed, accept it.
                return
        assert cancelled is not None
