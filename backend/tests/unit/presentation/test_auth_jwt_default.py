"""TDD tests for JWT being the default auth mode and embedding permissions."""

from __future__ import annotations

from fastapi.testclient import TestClient
from jose import jwt


def test_default_auth_mode_requires_bearer_token() -> None:
    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    denied = client.post(
        "/v1/tool-runs",
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert denied.status_code == 401


def test_login_token_contains_permissions_claim(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    monkeypatch.delenv("AUTH_MODE", raising=False)
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_USERS", "developer:developerpass:developer")

    client = TestClient(create_app())

    login = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert "perms" in payload
    assert "tool:execute" in payload["perms"]
