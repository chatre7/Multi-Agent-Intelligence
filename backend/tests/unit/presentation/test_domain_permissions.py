"""TDD tests for domain listing permissions."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_domains_list_requires_domain_read_permission() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer;user:userpass:user"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    user_token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]

    denied = client.get(
        "/v1/domains", headers={"authorization": f"Bearer {user_token}"}
    )
    assert denied.status_code == 403

    ok = client.get("/v1/domains", headers={"authorization": f"Bearer {dev_token}"})
    assert ok.status_code == 200
    assert isinstance(ok.json(), list)
