from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.domain.entities.knowledge import KnowledgeDocument
from src.domain.repositories.knowledge_repository import IKnowledgeRepository

@dataclass
class SqliteKnowledgeRepository(IKnowledgeRepository):
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
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

    def save(self, document: KnowledgeDocument) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_documents (
                    id, filename, content, content_type, size_bytes,
                    status, metadata_json, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')
                )
                ON CONFLICT(id) DO UPDATE SET
                    filename = excluded.filename,
                    content = excluded.content,
                    content_type = excluded.content_type,
                    size_bytes = excluded.size_bytes,
                    status = excluded.status,
                    metadata_json = excluded.metadata_json,
                    updated_at = datetime('now')
                """,
                (
                    document.id,
                    document.filename,
                    document.content,
                    document.content_type,
                    document.size_bytes,
                    document.status,
                    json.dumps(document.metadata),
                    document.created_at.isoformat() if isinstance(document.created_at, datetime) else document.created_at,
                ),
            )

    def get_by_id(self, document_id: str) -> Optional[KnowledgeDocument]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_documents WHERE id = ?", (document_id,)
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> List[KnowledgeDocument]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge_documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, document_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))

    def _from_row(self, row: sqlite3.Row) -> KnowledgeDocument:
        return KnowledgeDocument(
            id=row["id"],
            filename=row["filename"],
            content=row["content"],
            content_type=row["content_type"],
            size_bytes=int(row["size_bytes"]),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata_json"])
        )
