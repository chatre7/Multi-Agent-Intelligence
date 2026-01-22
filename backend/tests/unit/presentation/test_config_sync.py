"""TDD tests for config sync/status endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_config_status_and_sync_detect_changes() -> None:
    import os

    tmp_path = Path.cwd() / ".test_tmp" / f"config_sync_{uuid4()}"
    prev_auth_mode = os.environ.get("AUTH_MODE")
    prev_config_root = os.environ.get("CONFIG_ROOT")
    os.environ["AUTH_MODE"] = "header"
    os.environ["CONFIG_ROOT"] = str(tmp_path / "configs")

    try:
        _write(
            tmp_path / "configs" / "domains" / "demo.yaml",
            "\n".join(
                [
                    "id: demo",
                    "name: Demo",
                    "description: Demo domain",
                    "agents: [demo_agent]",
                    "default_agent: demo_agent",
                    "allowed_roles: [developer, admin]",
                ]
            )
            + "\n",
        )
        _write(
            tmp_path / "configs" / "agents" / "core" / "demo_agent.yaml",
            "\n".join(
                [
                    "id: demo_agent",
                    "name: DemoAgent",
                    "domain_id: demo",
                    "description: Demo agent",
                    "version: 1.0.0",
                    "state: development",
                    "system_prompt: ''",
                    "capabilities: []",
                    "tools: []",
                    "model_name: gpt-4o-mini",
                ]
            )
            + "\n",
        )
        _write(
            tmp_path / "configs" / "tools" / "demo.yaml",
            "\n".join(
                [
                    "id: demo_tool",
                    "name: DemoTool",
                    "description: Demo tool",
                    "parameters_schema: {type: object}",
                    "returns_schema: {type: object}",
                    "requires_approval: false",
                    "allowed_roles: [developer, admin]",
                ]
            )
            + "\n",
        )

        from src.presentation.api.app import create_app

        client = TestClient(create_app())
        headers = {"x-role": "developer"}

        status = client.get("/v1/config/status", headers=headers)
        assert status.status_code == 200
        status_payload = status.json()
        assert isinstance(status_payload.get("hash"), str)
        assert status_payload["hash"]

        sync_same = client.get(
            f"/v1/config/sync?since_hash={status_payload['hash']}", headers=headers
        )
        assert sync_same.status_code == 200
        assert sync_same.json()["changed"] is False

        # Modify a file, ensure hash changes and sync reports changed.
        _write(
            tmp_path / "configs" / "domains" / "demo.yaml",
            "\n".join(
                [
                    "id: demo",
                    "name: Demo",
                    "description: Demo domain UPDATED",
                    "agents: [demo_agent]",
                    "default_agent: demo_agent",
                    "allowed_roles: [developer, admin]",
                ]
            )
            + "\n",
        )

        sync_changed = client.get(
            f"/v1/config/sync?since_hash={status_payload['hash']}", headers=headers
        )
        assert sync_changed.status_code == 200
        changed_payload = sync_changed.json()
        assert changed_payload["changed"] is True
        assert changed_payload["hash"] != status_payload["hash"]
        assert "bundle" in changed_payload
    finally:
        if prev_auth_mode is None:
            os.environ.pop("AUTH_MODE", None)
        else:
            os.environ["AUTH_MODE"] = prev_auth_mode
        if prev_config_root is None:
            os.environ.pop("CONFIG_ROOT", None)
        else:
            os.environ["CONFIG_ROOT"] = prev_config_root
