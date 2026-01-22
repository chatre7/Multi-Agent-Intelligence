"""TDD tests for domain/agent/tool detail endpoints."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_get_agent_tool_domain_by_id_requires_permissions() -> None:
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

    user_headers = {"authorization": f"Bearer {user_token}"}
    dev_headers = {"authorization": f"Bearer {dev_token}"}

    # user has neither tool:read nor agent:read nor domain:read
    assert client.get("/v1/agents/coder", headers=user_headers).status_code == 403
    assert client.get("/v1/tools/save_file", headers=user_headers).status_code == 403
    assert (
        client.get("/v1/domains/software_development", headers=user_headers).status_code
        == 403
    )

    agent = client.get("/v1/agents/coder", headers=dev_headers)
    assert agent.status_code == 200
    assert agent.json()["id"] == "coder"

    tool = client.get("/v1/tools/save_file", headers=dev_headers)
    assert tool.status_code == 200
    assert tool.json()["id"] == "save_file"

    domain = client.get("/v1/domains/software_development", headers=dev_headers)
    assert domain.status_code == 200
    assert domain.json()["id"] == "software_development"


def test_get_unknown_ids_return_404() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "developer:developerpass:developer"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    dev_token = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "developerpass"}
    ).json()["access_token"]
    headers = {"authorization": f"Bearer {dev_token}"}

    assert client.get("/v1/agents/nope", headers=headers).status_code == 404
    assert client.get("/v1/tools/nope", headers=headers).status_code == 404
    assert client.get("/v1/domains/nope", headers=headers).status_code == 404
