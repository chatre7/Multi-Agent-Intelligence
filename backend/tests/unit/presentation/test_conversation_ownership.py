"""TDD tests for conversation ownership enforcement."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_user_cannot_read_other_users_conversation() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = (
        "alice:alicepass:user;bob:bobpass:user;developer:developerpass:developer"
    )

    from src.presentation.api.app import create_app

    client = TestClient(create_app())

    alice_token = client.post(
        "/v1/auth/login", json={"username": "alice", "password": "alicepass"}
    ).json()["access_token"]
    bob_token = client.post(
        "/v1/auth/login", json={"username": "bob", "password": "bobpass"}
    ).json()["access_token"]
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]

    alice_headers = {"authorization": f"Bearer {alice_token}"}
    bob_headers = {"authorization": f"Bearer {bob_token}"}
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    conversation_id = client.post(
        "/v1/chat",
        headers=alice_headers,
        json={"domain_id": "software_development", "message": "hello"},
    ).json()["conversation_id"]

    # Bob should not be able to read Alice's conversation
    denied = client.get(
        f"/v1/conversations/{conversation_id}/messages", headers=bob_headers
    )
    assert denied.status_code in (403, 404)

    # Developer can read
    ok = client.get(
        f"/v1/conversations/{conversation_id}/messages", headers=dev_headers
    )
    assert ok.status_code == 200
    assert any(m["role"] == "user" for m in ok.json())


def test_conversation_list_only_returns_own_for_user() -> None:
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

    alice_conv = client.post(
        "/v1/chat",
        headers=alice_headers,
        json={"domain_id": "software_development", "message": "alice"},
    ).json()["conversation_id"]
    bob_conv = client.post(
        "/v1/chat",
        headers=bob_headers,
        json={"domain_id": "software_development", "message": "bob"},
    ).json()["conversation_id"]

    alice_list = client.get("/v1/conversations?limit=50", headers=alice_headers).json()
    bob_list = client.get("/v1/conversations?limit=50", headers=bob_headers).json()

    assert any(c["id"] == alice_conv for c in alice_list)
    assert not any(c["id"] == bob_conv for c in alice_list)

    assert any(c["id"] == bob_conv for c in bob_list)
    assert not any(c["id"] == alice_conv for c in bob_list)
