"""TDD tests for conversation repo selection in create_app()."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_app_can_use_sqlite_conversation_repo_via_env(monkeypatch) -> None:
    from src.presentation.api.app import create_app

    db_uri = f"file:conv_app_{uuid4()}?mode=memory&cache=shared"
    monkeypatch.setenv("AUTH_MODE", "header")
    monkeypatch.setenv("CONVERSATION_REPO", "sqlite")
    monkeypatch.setenv("CONVERSATION_DB", db_uri)

    client = TestClient(create_app())
    chat = client.post(
        "/v1/chat",
        headers={"x-role": "user"},
        json={"domain_id": "software_development", "message": "hello"},
    )
    assert chat.status_code == 200
    conversation_id = chat.json()["conversation_id"]

    # New app instance should see persisted history in same shared DB
    client2 = TestClient(create_app())
    history = client2.get(f"/v1/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    assert any(m["role"] == "user" for m in history.json())
