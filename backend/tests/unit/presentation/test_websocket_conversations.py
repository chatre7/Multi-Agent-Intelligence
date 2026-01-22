"""TDD tests for conversation WebSocket events on /ws."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_ws_can_list_conversations_and_get_messages() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    # Create a conversation via REST
    conversation_id = client.post(
        "/v1/chat",
        headers=headers,
        json={"domain_id": "software_development", "message": "hello"},
    ).json()["conversation_id"]

    with client.websocket_connect("/ws", headers=headers) as ws:
        ws.send_json({"type": "conversation.list", "limit": 10})
        listed = ws.receive_json()
        assert listed["type"] == "conversation.listed"
        assert any(item["id"] == conversation_id for item in listed["conversations"])

        ws.send_json(
            {
                "type": "conversation.messages",
                "conversation_id": conversation_id,
                "limit": 50,
            }
        )
        msgs = ws.receive_json()
        assert msgs["type"] == "conversation.messages"
        assert msgs["conversation_id"] == conversation_id
        assert any(m["role"] == "user" for m in msgs["messages"])
        assert any(m["role"] == "assistant" for m in msgs["messages"])


def test_ws_conversation_list_invalid_cursor_errors() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    with client.websocket_connect("/ws", headers=headers) as ws:
        ws.send_json({"type": "conversation.list", "limit": 10, "cursor": "bad"})
        msg = ws.receive_json()
        assert msg["type"] == "error"


def test_ws_user_cannot_read_other_users_conversation() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "alice:alicepass:user;bob:bobpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    alice_token = client.post(
        "/v1/auth/login", json={"username": "alice", "password": "alicepass"}
    ).json()["access_token"]
    bob_token = client.post(
        "/v1/auth/login", json={"username": "bob", "password": "bobpass"}
    ).json()["access_token"]
    alice_headers = {"authorization": f"Bearer {alice_token}"}
    bob_headers = {"authorization": f"Bearer {bob_token}"}

    conversation_id = client.post(
        "/v1/chat",
        headers=alice_headers,
        json={"domain_id": "software_development", "message": "hello"},
    ).json()["conversation_id"]

    with client.websocket_connect("/ws", headers=bob_headers) as ws:
        ws.send_json(
            {
                "type": "conversation.messages",
                "conversation_id": conversation_id,
                "limit": 10,
            }
        )
        msg = ws.receive_json()
        assert msg["type"] == "error"
