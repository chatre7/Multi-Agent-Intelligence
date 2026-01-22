"""TDD tests for legacy /ws/chat endpoint auth in JWT mode."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_ws_chat_requires_bearer_token_in_jwt_mode() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/chat"):
            pass


def test_ws_chat_accepts_with_token_and_streams() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    with client.websocket_connect("/ws/chat", headers=headers) as ws:
        ws.send_json({"domain_id": "software_development", "message": "hello"})
        got_done = False
        for _ in range(50):
            msg = ws.receive_json()
            if msg["type"] == "done":
                got_done = True
                assert msg["message"]["conversation_id"]
                break
        assert got_done is True
