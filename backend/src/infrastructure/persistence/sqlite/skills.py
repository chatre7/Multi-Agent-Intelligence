from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.skill import Skill
from src.domain.repositories.skill_repository import ISkillRepository


@dataclass
class SqliteSkillRepository(ISkillRepository):
    """SQLite-backed Skill repository."""

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
        # Enforce foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                instructions TEXT NOT NULL,
                version TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_skills (
                agent_id TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (agent_id, skill_id),
                FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
            )
            """
        )

    def save(self, skill: Skill) -> None:
        row = self._to_row(skill)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO skills (
                    id, name, description, instructions, version,
                    tools_json, metadata_json, updated_at
                ) VALUES (
                    :id, :name, :description, :instructions, :version,
                    :tools_json, :metadata_json, datetime('now')
                )
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    instructions = excluded.instructions,
                    version = excluded.version,
                    tools_json = excluded.tools_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = datetime('now')
                """,
                row,
            )

    def get(self, skill_id: str) -> Skill | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE id = ?",
                (skill_id,),
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[Skill]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM skills ORDER BY name ASC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, skill_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))

    def add_skill_to_agent(self, agent_id: str, skill_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_skills (agent_id, skill_id, is_active)
                VALUES (?, ?, 1)
                ON CONFLICT(agent_id, skill_id) DO UPDATE SET is_active = 1
                """,
                (agent_id, skill_id),
            )

    def remove_skill_from_agent(self, agent_id: str, skill_id: str) -> None:
        # We can either soft delete (is_active=0) or hard delete
        # Let's hard delete for simplicity unless history is needed
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM agent_skills WHERE agent_id = ? AND skill_id = ?",
                (agent_id, skill_id),
            )

    def get_agent_skills(self, agent_id: str) -> list[Skill]:
        query = """
            SELECT s.*
            FROM skills s
            JOIN agent_skills link ON s.id = link.skill_id
            WHERE link.agent_id = ? AND link.is_active = 1
            ORDER BY s.name ASC
        """
        with self._connect() as conn:
            rows = conn.execute(query, (agent_id,)).fetchall()
        return [self._from_row(row) for row in rows]

    def _to_row(self, skill: Skill) -> dict:
        return {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "version": skill.version,
            "tools_json": json.dumps(skill.tools, ensure_ascii=False),
            "metadata_json": json.dumps(skill.metadata, ensure_ascii=False),
        }

    def _from_row(self, row: sqlite3.Row) -> Skill:
        return Skill(
            id=str(row["id"]),
            name=str(row["name"]),
            description=str(row["description"]),
            instructions=str(row["instructions"]),
            version=str(row["version"]),
            tools=json.loads(row["tools_json"]),
            metadata=json.loads(row["metadata_json"]),
        )
