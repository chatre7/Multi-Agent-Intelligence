"""SQLite ToolRun repository adapter (MVP)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.tool_run import ToolRun
from src.domain.repositories.tool_run_repository import IToolRunRepository
from src.domain.value_objects.tool_run_status import ToolRunStatus


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _cursor_for(run: ToolRun) -> str:
    return f"{run.updated_at.isoformat()}|{run.id}"


@dataclass
class SqliteToolRunRepository(IToolRunRepository):
    """SQLite-backed ToolRun repository."""

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

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_runs (
              id TEXT PRIMARY KEY,
              tool_id TEXT NOT NULL,
              parameters_json TEXT NOT NULL,
              requested_by_role TEXT NOT NULL,
              requested_by_sub TEXT NOT NULL,
              conversation_id TEXT NOT NULL,
              requires_approval INTEGER NOT NULL,
              status TEXT NOT NULL,
              approved_by_role TEXT,
              approved_at TEXT,
              rejected_by_role TEXT,
              rejected_at TEXT,
              rejection_reason TEXT,
              executed_by_role TEXT,
              executed_at TEXT,
              result_json TEXT NOT NULL,
              error TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(tool_runs)").fetchall()
        }
        if "requested_by_sub" not in existing_columns:
            conn.execute(
                "ALTER TABLE tool_runs ADD COLUMN requested_by_sub TEXT NOT NULL DEFAULT ''"
            )
        if "conversation_id" not in existing_columns:
            conn.execute(
                "ALTER TABLE tool_runs ADD COLUMN conversation_id TEXT NOT NULL DEFAULT ''"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_runs_updated_at ON tool_runs(updated_at DESC, id DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_runs_status ON tool_runs(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_runs_tool_id ON tool_runs(tool_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_runs_requested_by_sub ON tool_runs(requested_by_sub)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_runs_conversation_id ON tool_runs(conversation_id)"
        )

    def close(self) -> None:
        """Close the keepalive connection if present."""
        if self._keepalive_conn is not None:
            try:
                self._keepalive_conn.close()
            finally:
                self._keepalive_conn = None

    def _connect(self) -> sqlite3.Connection:
        conn = self._open_connection()
        conn.row_factory = sqlite3.Row
        return conn

    def _open_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            uri=self.db_path.startswith("file:"),
        )

    def add(self, tool_run: ToolRun) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tool_runs (
                  id, tool_id, parameters_json, requested_by_role, requested_by_sub, conversation_id, requires_approval, status,
                  approved_by_role, approved_at, rejected_by_role, rejected_at, rejection_reason,
                  executed_by_role, executed_at, result_json, error, created_at, updated_at
                ) VALUES (
                  :id, :tool_id, :parameters_json, :requested_by_role, :requested_by_sub, :conversation_id, :requires_approval, :status,
                  :approved_by_role, :approved_at, :rejected_by_role, :rejected_at, :rejection_reason,
                  :executed_by_role, :executed_at, :result_json, :error, :created_at, :updated_at
                )
                """,
                self._to_row(tool_run),
            )

    def get(self, run_id: str) -> ToolRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tool_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def update(self, tool_run: ToolRun) -> None:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tool_runs SET
                  tool_id = :tool_id,
                  parameters_json = :parameters_json,
                  requested_by_role = :requested_by_role,
                  requested_by_sub = :requested_by_sub,
                  conversation_id = :conversation_id,
                  requires_approval = :requires_approval,
                  status = :status,
                  approved_by_role = :approved_by_role,
                  approved_at = :approved_at,
                  rejected_by_role = :rejected_by_role,
                  rejected_at = :rejected_at,
                  rejection_reason = :rejection_reason,
                  executed_by_role = :executed_by_role,
                  executed_at = :executed_at,
                  result_json = :result_json,
                  error = :error,
                  created_at = :created_at,
                  updated_at = :updated_at
                WHERE id = :id
                """,
                self._to_row(tool_run),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Unknown tool run id: {tool_run.id}")

    def list_recent(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        tool_id: str | None = None,
        requested_by_sub: str | None = None,
        cursor: str | None = None,
    ) -> list[ToolRun]:
        query = "SELECT * FROM tool_runs"
        clauses: list[str] = []
        params: list[object] = []

        if status is not None:
            clauses.append("status = ?")
            params.append(status.lower())
        if tool_id is not None:
            clauses.append("tool_id = ?")
            params.append(tool_id)
        if requested_by_sub is not None:
            clauses.append("requested_by_sub = ?")
            params.append(requested_by_sub)

        if cursor:
            updated_at, run_id = cursor.split("|", 1)
            clauses.append("(updated_at < ? OR (updated_at = ? AND id < ?))")
            params.extend([updated_at, updated_at, run_id])

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
        params.append(int(limit))

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._from_row(row) for row in rows]

    def get_next_cursor(self, runs: list[ToolRun], *, has_more: bool) -> str | None:
        if not has_more or not runs:
            return None
        return _cursor_for(runs[-1])

    def _to_row(self, tool_run: ToolRun) -> dict:
        return {
            "id": tool_run.id,
            "tool_id": tool_run.tool_id,
            "parameters_json": json.dumps(tool_run.parameters, ensure_ascii=False),
            "requested_by_role": tool_run.requested_by_role,
            "requested_by_sub": tool_run.requested_by_sub,
            "conversation_id": tool_run.conversation_id,
            "requires_approval": 1 if tool_run.requires_approval else 0,
            "status": tool_run.status.value,
            "approved_by_role": tool_run.approved_by_role,
            "approved_at": _iso(tool_run.approved_at),
            "rejected_by_role": tool_run.rejected_by_role,
            "rejected_at": _iso(tool_run.rejected_at),
            "rejection_reason": tool_run.rejection_reason,
            "executed_by_role": tool_run.executed_by_role,
            "executed_at": _iso(tool_run.executed_at),
            "result_json": json.dumps(tool_run.result, ensure_ascii=False),
            "error": tool_run.error,
            "created_at": tool_run.created_at.isoformat(),
            "updated_at": tool_run.updated_at.isoformat(),
        }

    def _from_row(self, row: sqlite3.Row) -> ToolRun:
        return ToolRun(
            id=str(row["id"]),
            tool_id=str(row["tool_id"]),
            parameters=json.loads(row["parameters_json"] or "{}"),
            requested_by_role=str(row["requested_by_role"]),
            requested_by_sub=str(row["requested_by_sub"] or ""),
            conversation_id=str(row["conversation_id"] or ""),
            requires_approval=bool(row["requires_approval"]),
            status=ToolRunStatus.from_string(str(row["status"])),
            approved_by_role=row["approved_by_role"],
            approved_at=_parse_iso(row["approved_at"]),
            rejected_by_role=row["rejected_by_role"],
            rejected_at=_parse_iso(row["rejected_at"]),
            rejection_reason=row["rejection_reason"],
            executed_by_role=row["executed_by_role"],
            executed_at=_parse_iso(row["executed_at"]),
            result=json.loads(row["result_json"] or "{}"),
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
