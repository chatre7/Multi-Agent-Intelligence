"""TDD tests for config reload endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_config_reload_requires_admin_or_developer() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "admin:adminpass:admin;user:userpass:user"

    client = TestClient(create_app())

    user_token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    denied = client.post(
        "/v1/config/reload", headers={"authorization": f"Bearer {user_token}"}, json={}
    )
    assert denied.status_code == 403

    admin_token = client.post(
        "/v1/auth/login", json={"username": "admin", "password": "adminpass"}
    ).json()["access_token"]
    ok = client.post(
        "/v1/config/reload", headers={"authorization": f"Bearer {admin_token}"}, json={}
    )
    assert ok.status_code == 200
    assert ok.json()["ok"] is True
