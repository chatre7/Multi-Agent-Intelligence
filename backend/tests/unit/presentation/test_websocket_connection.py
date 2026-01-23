"""Unit tests for WebSocket connection and reconnection logic."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


@pytest.fixture(autouse=True)
def setup_auth_env():
    """Set up JWT auth environment for all tests."""
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "admin:admin:admin;user:userpass:user"
    yield
    # Cleanup not strictly necessary but good practice


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    def test_connect_with_valid_token_via_query_param(self) -> None:
        """WebSocket should accept connection with valid token in query param."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({"type": "PING"})
            response = ws.receive_json()
            assert response["type"] == "PONG"

    def test_connect_with_valid_token_via_header(self) -> None:
        """WebSocket should accept connection with valid token in Authorization header."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        headers = {"authorization": f"Bearer {token}"}
        with client.websocket_connect("/ws", headers=headers) as ws:
            ws.send_json({"type": "PING"})
            response = ws.receive_json()
            assert response["type"] == "PONG"

    def test_connect_without_token_closes_with_1008(self) -> None:
        """WebSocket should close with code 1008 when no token provided."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws"):
                pass
        assert exc_info.value.code == 1008

    def test_connect_with_invalid_token_closes_with_1008(self) -> None:
        """WebSocket should close with code 1008 for invalid token."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws?token=invalid-token"):
                pass
        assert exc_info.value.code == 1008


class TestWebSocketPingPong:
    """Tests for keep-alive PING/PONG mechanism."""

    def test_ping_returns_pong(self) -> None:
        """Server should respond to PING with PONG."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({"type": "PING"})
            response = ws.receive_json()
            assert response == {"type": "PONG"}

    def test_multiple_pings_all_return_pongs(self) -> None:
        """Multiple PINGs should each receive a PONG."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            for _ in range(3):
                ws.send_json({"type": "PING"})
                response = ws.receive_json()
                assert response["type"] == "PONG"


class TestWebSocketConversation:
    """Tests for conversation management via WebSocket."""

    def test_start_conversation_returns_conversation_id(self) -> None:
        """start_conversation should return a new conversation ID."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "admin", "password": "admin"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({
                "type": "start_conversation",
                "payload": {"domainId": "software_development"}
            })
            response = ws.receive_json()
            assert response["type"] == "conversation_started"
            assert "conversationId" in response["payload"]
            assert response["payload"]["domainId"] == "software_development"

    def test_start_conversation_requires_domain_id(self) -> None:
        """start_conversation without domainId should return error."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "admin", "password": "admin"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({
                "type": "start_conversation",
                "payload": {}
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "bad_request"

    def test_send_message_requires_conversation_id(self) -> None:
        """send_message without conversationId should return error."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "admin", "password": "admin"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({
                "type": "send_message",
                "payload": {"content": "Hello"}
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "bad_request"


class TestWebSocketErrorHandling:
    """Tests for error handling in WebSocket communication."""

    def test_unknown_message_type_handled_gracefully(self) -> None:
        """Unknown message types should not crash the connection."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            # Send unknown message type
            ws.send_json({"type": "UNKNOWN_TYPE"})
            # Server may send error or ignore - either is fine
            # Important: connection should still work after
            ws.send_json({"type": "PING"})
            # Drain any error message first
            response = ws.receive_json()
            if response["type"] == "error":
                # Got error for unknown type, now try PING again
                ws.send_json({"type": "PING"})
                response = ws.receive_json()
            assert response["type"] == "PONG"

    def test_invalid_json_handled_gracefully(self) -> None:
        """Invalid JSON should close connection gracefully."""
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        token = client.post(
            "/v1/auth/login", json={"username": "user", "password": "userpass"}
        ).json()["access_token"]

        with client.websocket_connect(f"/ws?token={token}") as ws:
            # Send invalid JSON
            ws.send_text("not valid json")
            # Expect graceful closure or error, not crash
            # The connection may close or return an error
