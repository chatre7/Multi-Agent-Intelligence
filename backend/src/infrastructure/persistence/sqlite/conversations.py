"""SQLite ConversationRepository adapter (MVP)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.repositories.conversation_repository import IConversationRepository
from src.infrastructure.persistence.sqlite.schema import init_schema


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _cursor_for(conversation: Conversation) -> str:
    return f"{conversation.updated_at.isoformat()}|{conversation.id}"


@dataclass
class SqliteConversationRepository(IConversationRepository):
    """SQLite-backed repository for conversations and messages."""

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

    def create_conversation(self, conversation: Conversation) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (
                    id, domain_id, created_by_role, created_by_sub,
                    title, status, reviewers,
                    created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation.id,
                    conversation.domain_id,
                    conversation.created_by_role,
                    conversation.created_by_sub,
                    conversation.title,
                    conversation.status.value,
                    json.dumps(conversation.reviewers),
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                    json.dumps(conversation.metadata),
                ),
            )

    def update_conversation(self, conversation: Conversation) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE conversations
                SET domain_id = ?, created_by_role = ?, created_by_sub = ?,
                    title = ?, status = ?, reviewers = ?,
                    updated_at = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    conversation.domain_id,
                    conversation.created_by_role,
                    conversation.created_by_sub,
                    conversation.title,
                    conversation.status.value,
                    json.dumps(conversation.reviewers),
                    conversation.updated_at.isoformat(),
                    json.dumps(conversation.metadata),
                    conversation.id,
                ),
            )

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        if row is None:
            return None
        return Conversation(
            id=str(row["id"]),
            domain_id=str(row["domain_id"]),
            created_by_role=str(row["created_by_role"]),
            created_by_sub=str(row["created_by_sub"]),
            title=row["title"],
            status=Conversation.ThreadStatus(row["status"]),
            reviewers=json.loads(row["reviewers"]) if row["reviewers"] else [],
            created_at=_parse_iso(str(row["created_at"])),
            updated_at=_parse_iso(str(row["updated_at"])),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def add_message(self, message: Message) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    message.created_at.isoformat(),
                    json.dumps(message.metadata),
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now().astimezone().isoformat(), message.conversation_id),
            )

    def list_messages(self, conversation_id: str, limit: int = 200) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (conversation_id, int(limit)),
            ).fetchall()
        return [
            Message(
                id=str(row["id"]),
                conversation_id=str(row["conversation_id"]),
                role=str(row["role"]),
                content=str(row["content"]),
                created_at=_parse_iso(str(row["created_at"])),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

    def list_conversations(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        domain_id: str | None = None,
        created_by_sub: str | None = None,
    ) -> list[Conversation]:
        query = "SELECT * FROM conversations"
        clauses: list[str] = []
        params: list[object] = []

        if domain_id is not None:
            clauses.append("domain_id = ?")
            params.append(domain_id)
        if created_by_sub is not None:
            clauses.append("created_by_sub = ?")
            params.append(created_by_sub)

        if cursor:
            cursor = cursor.strip().replace(" ", "+")
            updated_at, convo_id = cursor.split("|", 1)
            clauses.append("(updated_at < ? OR (updated_at = ? AND id < ?))")
            params.extend([updated_at, updated_at, convo_id])

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
        params.append(int(limit))

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [
            Conversation(
                id=str(row["id"]),
                domain_id=str(row["domain_id"]),
                created_by_role=str(row["created_by_role"]),
                created_by_sub=str(row["created_by_sub"]),
                title=row["title"],
                status=Conversation.ThreadStatus(row["status"]),
                reviewers=json.loads(row["reviewers"]) if row["reviewers"] else [],
                created_at=_parse_iso(str(row["created_at"])),
                updated_at=_parse_iso(str(row["updated_at"])),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

    def get_next_cursor(
        self, conversations: list[Conversation], *, has_more: bool
    ) -> str | None:
        if not has_more or not conversations:
            return None
        return _cursor_for(conversations[-1])
