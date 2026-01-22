"""TDD tests for optional JWT auth mode."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_jwt_mode_requires_token_for_tool_runs(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    monkeypatch.setenv("AUTH_MODE", "jwt")
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_USERS", "admin:adminpass:admin")

    client = TestClient(create_app())

    denied = client.post(
        "/v1/tool-runs",
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert denied.status_code == 401


def test_login_and_access_with_bearer_token(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    monkeypatch.setenv("AUTH_MODE", "jwt")
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_USERS", "admin:adminpass:admin")

    client = TestClient(create_app())

    login = client.post(
        "/v1/auth/login", json={"username": "admin", "password": "adminpass"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    created = client.post(
        "/v1/tool-runs",
        headers={"authorization": f"Bearer {token}"},
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    assert created.status_code == 200
