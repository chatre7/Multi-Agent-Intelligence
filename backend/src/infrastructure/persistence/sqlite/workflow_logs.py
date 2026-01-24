from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.domain.entities.workflow_log import WorkflowLog
from src.domain.repositories.workflow_log_repository import IWorkflowLogRepository
from src.infrastructure.persistence.sqlite.schema import init_schema

def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)

@dataclass
class SqliteWorkflowLogRepository(IWorkflowLogRepository):
    """SQLite-backed repository for workflow logs."""

    db_path: str
    _keepalive_conn: sqlite3.Connection | None = None

    def __post_init__(self) -> None:
        if self._is_memory_uri():
            self._keepalive_conn = self._open_connection()
            self._keepalive_conn.execute("PRAGMA journal_mode=WAL")
            init_schema(self._keepalive_conn)
        else:
            with self._connect() as conn:
                init_schema(conn)

    def _is_memory_uri(self) -> bool:
        return self.db_path.startswith("file:") and "mode=memory" in self.db_path

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

    def close(self) -> None:
        if self._keepalive_conn is not None:
            try:
                self._keepalive_conn.close()
            finally:
                self._keepalive_conn = None

    def save(self, log: WorkflowLog) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_logs (id, conversation_id, agent_id, agent_name, event_type, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.conversation_id,
                    log.agent_id,
                    log.agent_name,
                    log.event_type,
                    log.content,
                    json.dumps(log.metadata),
                    log.created_at.isoformat(),
                ),
            )

    def list_by_conversation(self, conversation_id: str, limit: int = 100) -> List[WorkflowLog]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM workflow_logs
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        
        return [
            WorkflowLog(
                id=str(row["id"]),
                conversation_id=str(row["conversation_id"]),
                agent_id=str(row["agent_id"]),
                agent_name=str(row["agent_name"]),
                event_type=str(row["event_type"]),
                content=str(row["content"]) if row["content"] else None,
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=_parse_iso(str(row["created_at"])),
            )
            for row in rows
        ]

    def delete(self, log_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM workflow_logs WHERE id = ?", (log_id,))
