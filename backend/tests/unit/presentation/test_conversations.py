"""TDD tests for conversation persistence and endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_creates_conversation_and_persists_messages() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    chat = client.post(
        "/v1/chat",
        headers=headers,
        json={"domain_id": "software_development", "message": "hello"},
    )
    assert chat.status_code == 200
    data = chat.json()
    assert "conversation_id" in data
    conversation_id = data["conversation_id"]
    assert conversation_id

    history = client.get(
        f"/v1/conversations/{conversation_id}/messages", headers=headers
    )
    assert history.status_code == 200
    messages = history.json()
    assert isinstance(messages, list)
    assert any(m["role"] == "user" and "hello" in m["content"] for m in messages)
    assert any(m["role"] == "assistant" for m in messages)


def test_chat_with_existing_conversation_appends() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    chat1 = client.post(
        "/v1/chat",
        headers=headers,
        json={"domain_id": "software_development", "message": "first"},
    )
    conversation_id = chat1.json()["conversation_id"]

    chat2 = client.post(
        "/v1/chat",
        headers=headers,
        json={
            "domain_id": "software_development",
            "message": "second",
            "conversation_id": conversation_id,
        },
    )
    assert chat2.status_code == 200
    assert chat2.json()["conversation_id"] == conversation_id

    history = client.get(
        f"/v1/conversations/{conversation_id}/messages", headers=headers
    )
    assert history.status_code == 200
    messages = history.json()
    assert sum(1 for m in messages if m["role"] == "user") >= 2
