"""TDD tests for SQLite RegisteredAgent repository adapter."""

from __future__ import annotations

from uuid import uuid4

from src.domain.entities.registered_agent import RegisteredAgent
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


def test_sqlite_registered_agent_roundtrip_and_updates() -> None:
    from src.infrastructure.persistence.sqlite.registered_agents import (
        SqliteRegisteredAgentRepository,
    )

    db_uri = f"file:registered_agents_{uuid4()}?mode=memory&cache=shared"
    repo = SqliteRegisteredAgentRepository(db_path=db_uri)

    agent = RegisteredAgent(
        id="remote",
        name="Remote",
        description="d",
        endpoint="http://localhost:1234",
        version=SemanticVersion.from_string("1.2.3"),
        state=AgentState.DEVELOPMENT,
        capabilities=["code"],
    )
    repo.upsert(agent)

    loaded = repo.get("remote")
    assert loaded is not None
    assert loaded.id == "remote"
    assert str(loaded.version) == "1.2.3"
    assert loaded.state == AgentState.DEVELOPMENT
    assert loaded.capabilities == ["code"]

    loaded.bump_version("patch")
    loaded.promote(AgentState.TESTING)
    repo.upsert(loaded)

    loaded2 = repo.get("remote")
    assert loaded2 is not None
    assert str(loaded2.version) == "1.2.4"
    assert loaded2.state == AgentState.TESTING
