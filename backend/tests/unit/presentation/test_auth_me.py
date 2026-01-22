"""TDD tests for /v1/auth/me endpoint."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_auth_me_requires_token_in_jwt_mode() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_auth_me_returns_role_and_permissions() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    me = client.get("/v1/auth/me", headers={"authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["role"] == "developer"
    assert "perms" in data
    assert "tool:execute" in data["perms"]
