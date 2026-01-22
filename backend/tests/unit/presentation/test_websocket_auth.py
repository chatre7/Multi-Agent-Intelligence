"""TDD tests for WebSocket auth in JWT mode."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_ws_requires_bearer_token_in_jwt_mode() -> None:
    from src.presentation.api.app import create_app

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    client = TestClient(create_app())

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass
