"""TDD tests for detailed health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_details_includes_modes_and_config_counts() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer"

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    resp = client.get("/health/details", headers={"authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["ok"] is True
    assert "auth_mode" in data
    assert "conversation_repo" in data
    assert "tool_run_repo" in data
    assert "config_counts" in data
    assert data["config_counts"]["domains"] >= 1
    assert data["config_counts"]["agents"] >= 1
    assert data["config_counts"]["tools"] >= 1
