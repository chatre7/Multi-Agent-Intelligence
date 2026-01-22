"""TDD tests for agent registry and versioning endpoints (MVP)."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_developer_can_register_and_promote_agent() -> None:
    prev_auth_mode = os.environ.get("AUTH_MODE")
    os.environ["AUTH_MODE"] = "header"

    try:
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        headers = {"x-role": "developer"}

        created = client.post(
            "/v1/registry/agents",
            headers=headers,
            json={
                "id": "remote_coder",
                "name": "RemoteCoder",
                "description": "Remote coding agent",
                "endpoint": "http://localhost:9000",
                "version": "1.0.0",
                "state": "development",
                "capabilities": ["code", "review"],
            },
        )
        assert created.status_code == 200
        payload = created.json()
        assert payload["id"] == "remote_coder"
        assert payload["version"] == "1.0.0"
        assert payload["state"] == "development"

        promoted = client.post(
            "/v1/registry/agents/remote_coder/promote",
            headers=headers,
            json={"state": "testing"},
        )
        assert promoted.status_code == 200
        assert promoted.json()["state"] == "testing"

        promoted2 = client.post(
            "/v1/registry/agents/remote_coder/promote",
            headers=headers,
            json={"state": "production"},
        )
        assert promoted2.status_code == 200
        assert promoted2.json()["state"] == "production"

        invalid = client.post(
            "/v1/registry/agents/remote_coder/promote",
            headers=headers,
            json={"state": "development"},
        )
        assert invalid.status_code == 400
    finally:
        if prev_auth_mode is None:
            os.environ.pop("AUTH_MODE", None)
        else:
            os.environ["AUTH_MODE"] = prev_auth_mode


def test_user_cannot_register_agent() -> None:
    prev_auth_mode = os.environ.get("AUTH_MODE")
    os.environ["AUTH_MODE"] = "header"

    try:
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        denied = client.post(
            "/v1/registry/agents",
            headers={"x-role": "user"},
            json={
                "id": "x",
                "name": "X",
                "description": "x",
                "endpoint": "",
                "version": "1.0.0",
                "state": "development",
                "capabilities": [],
            },
        )
        assert denied.status_code == 403
    finally:
        if prev_auth_mode is None:
            os.environ.pop("AUTH_MODE", None)
        else:
            os.environ["AUTH_MODE"] = prev_auth_mode


def test_bump_version_patch() -> None:
    prev_auth_mode = os.environ.get("AUTH_MODE")
    os.environ["AUTH_MODE"] = "header"

    try:
        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        headers = {"x-role": "developer"}
        client.post(
            "/v1/registry/agents",
            headers=headers,
            json={
                "id": "agent_v",
                "name": "AgentV",
                "description": "v",
                "endpoint": "",
                "version": "1.2.3",
                "state": "development",
                "capabilities": [],
            },
        )

        bumped = client.post(
            "/v1/registry/agents/agent_v/version/bump",
            headers=headers,
            json={"kind": "patch"},
        )
        assert bumped.status_code == 200
        assert bumped.json()["version"] == "1.2.4"

        listed = client.get("/v1/registry/agents", headers=headers)
        assert listed.status_code == 200
        assert any(a["id"] == "agent_v" for a in listed.json())

        fetched = client.get("/v1/registry/agents/agent_v", headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()["id"] == "agent_v"

        heartbeat = client.post(
            "/v1/registry/agents/agent_v/heartbeat", headers=headers, json={}
        )
        assert heartbeat.status_code == 200
        assert heartbeat.json()["last_heartbeat_at"] is not None
    finally:
        if prev_auth_mode is None:
            os.environ.pop("AUTH_MODE", None)
        else:
            os.environ["AUTH_MODE"] = prev_auth_mode
