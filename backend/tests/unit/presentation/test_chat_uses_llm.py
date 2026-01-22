"""TDD test that /v1/chat uses LLM output by default."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_chat_reply_comes_from_llm_provider() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"
    os.environ["AUTH_USERS"] = "user:userpass:user"
    os.environ["LLM_PROVIDER"] = "deterministic"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    token = client.post(
        "/v1/auth/login", json={"username": "user", "password": "userpass"}
    ).json()["access_token"]

    resp = client.post(
        "/v1/chat",
        headers={"authorization": f"Bearer {token}"},
        json={"domain_id": "software_development", "message": "hello"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["reply"].startswith("LLM(")
