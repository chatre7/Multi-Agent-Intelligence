"""TDD tests for listing conversations endpoint."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_list_conversations_requires_chat_read_and_paginates() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    # Create two conversations
    first = client.post(
        "/v1/chat",
        headers=headers,
        json={"domain_id": "software_development", "message": "first"},
    ).json()["conversation_id"]
    second = client.post(
        "/v1/chat",
        headers=headers,
        json={"domain_id": "software_development", "message": "second"},
    ).json()["conversation_id"]
    assert first != second

    page1 = client.get("/v1/conversations?limit=1", headers=headers)
    assert page1.status_code == 200
    assert isinstance(page1.json(), list)
    assert len(page1.json()) == 1
    cursor = page1.headers.get("x-next-cursor")
    assert cursor is not None

    page2 = client.get(f"/v1/conversations?limit=1&cursor={cursor}", headers=headers)
    assert page2.status_code == 200
    assert len(page2.json()) == 1
    ids = {page1.json()[0]["id"], page2.json()[0]["id"]}
    assert first in ids
    assert second in ids


def test_list_conversations_invalid_cursor_returns_400() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}

    resp = client.get("/v1/conversations?cursor=bad", headers=headers)
    assert resp.status_code == 400
