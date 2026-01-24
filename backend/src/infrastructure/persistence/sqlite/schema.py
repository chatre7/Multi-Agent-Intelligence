"""SQLite schema initialization for Chat persistence."""

import sqlite3


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize the database schema for conversations and messages."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            domain_id TEXT NOT NULL,
            created_by_role TEXT NOT NULL,
            created_by_sub TEXT NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT  -- JSON string
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT, -- JSON string
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at ASC, id ASC)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_logs (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            content TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_workflow_logs_conv_created ON workflow_logs(conversation_id, created_at ASC)"
    )
