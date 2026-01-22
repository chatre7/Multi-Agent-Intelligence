"""TDD tests for chat events on the /ws multiplexer."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_websocket_chat_send_returns_conversation_id() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    with client.websocket_connect("/ws", headers=headers) as ws:
        ws.send_json(
            {
                "type": "chat.send",
                "domain_id": "software_development",
                "message": "hello",
            }
        )

        # Expect streaming deltas then done
        done = None
        for _ in range(50):
            msg = ws.receive_json()
            if msg["type"] == "chat.done":
                done = msg
                break
        assert done is not None
        assert done["message"]["conversation_id"]

        conversation_id = done["message"]["conversation_id"]

        ws.send_json(
            {
                "type": "chat.send",
                "domain_id": "software_development",
                "message": "second",
                "conversation_id": conversation_id,
            }
        )
        done2 = None
        for _ in range(50):
            msg = ws.receive_json()
            if msg["type"] == "chat.done":
                done2 = msg
                break
        assert done2 is not None
        assert done2["message"]["conversation_id"] == conversation_id
