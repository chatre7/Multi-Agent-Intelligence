"""TDD tests for Prometheus metrics endpoint and counters."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_metrics_endpoint_exposes_custom_counters() -> None:
    import os

    from src.presentation.api.app import create_app

    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer;user:userpass:user"

    client = TestClient(create_app())
    user_token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    user_headers = {"authorization": f"Bearer {user_token}"}
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    # Hit some endpoints to increment counters
    client.post(
        "/v1/tool-runs",
        headers=user_headers,
        json={
            "tool_id": "save_file",
            "parameters": {"path": "x.txt", "content": "hello"},
        },
    )
    client.post(
        "/v1/chat",
        headers=user_headers,
        json={"domain_id": "software_development", "message": "hello"},
    )

    metrics = client.get("/metrics", headers=dev_headers)
    assert metrics.status_code == 200
    body = metrics.text

    assert "multi_agent_tool_runs_requested_total" in body
    assert "multi_agent_chat_messages_total" in body
