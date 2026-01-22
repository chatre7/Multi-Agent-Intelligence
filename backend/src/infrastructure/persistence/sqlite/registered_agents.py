"""SQLite RegisteredAgent repository adapter (MVP)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.registered_agent import RegisteredAgent
from src.domain.repositories.registered_agent_repository import (
    IRegisteredAgentRepository,
)
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@dataclass
class SqliteRegisteredAgentRepository(IRegisteredAgentRepository):
    """SQLite-backed RegisteredAgent repository."""

    db_path: str
    _keepalive_conn: sqlite3.Connection | None = None

    def __post_init__(self) -> None:
        if self._is_memory_uri():
            self._keepalive_conn = self._open_connection()
            self._keepalive_conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema(self._keepalive_conn)
        else:
            with self._connect() as conn:
                self._init_schema(conn)

    def _is_memory_uri(self) -> bool:
        return self.db_path.startswith("file:") and "mode=memory" in self.db_path

    def close(self) -> None:
        if self._keepalive_conn is not None:
            try:
                self._keepalive_conn.close()
            finally:
                self._keepalive_conn = None

    def _open_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            uri=self.db_path.startswith("file:"),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = self._open_connection()
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registered_agents (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT NOT NULL,
              endpoint TEXT NOT NULL,
              version TEXT NOT NULL,
              state TEXT NOT NULL,
              capabilities_json TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              last_heartbeat_at TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_registered_agents_name ON registered_agents(name)"
        )

    def upsert(self, agent: RegisteredAgent) -> None:
        row = self._to_row(agent)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO registered_agents (
                  id, name, description, endpoint, version, state,
                  capabilities_json, metadata_json, last_heartbeat_at,
                  created_at, updated_at
                ) VALUES (
                  :id, :name, :description, :endpoint, :version, :state,
                  :capabilities_json, :metadata_json, :last_heartbeat_at,
                  :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                  name = excluded.name,
                  description = excluded.description,
                  endpoint = excluded.endpoint,
                  version = excluded.version,
                  state = excluded.state,
                  capabilities_json = excluded.capabilities_json,
                  metadata_json = excluded.metadata_json,
                  last_heartbeat_at = excluded.last_heartbeat_at,
                  updated_at = excluded.updated_at
                """,
                row,
            )

    def get(self, agent_id: str) -> RegisteredAgent | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM registered_agents WHERE id = ?",
                (agent_id,),
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[RegisteredAgent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM registered_agents ORDER BY name ASC, id ASC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def _to_row(self, agent: RegisteredAgent) -> dict:
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "endpoint": agent.endpoint,
            "version": str(agent.version),
            "state": agent.state.value,
            "capabilities_json": json.dumps(
                list(agent.capabilities), ensure_ascii=False
            ),
            "metadata_json": json.dumps(dict(agent.metadata), ensure_ascii=False),
            "last_heartbeat_at": _iso(agent.last_heartbeat_at),
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
        }

    def _from_row(self, row: sqlite3.Row) -> RegisteredAgent:
        return RegisteredAgent(
            id=str(row["id"]),
            name=str(row["name"]),
            description=str(row["description"]),
            endpoint=str(row["endpoint"]),
            version=SemanticVersion.from_string(str(row["version"])),
            state=AgentState.from_string(str(row["state"])),
            capabilities=list(json.loads(row["capabilities_json"] or "[]")),
            metadata=dict(json.loads(row["metadata_json"] or "{}")),
            last_heartbeat_at=_parse_iso(row["last_heartbeat_at"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
