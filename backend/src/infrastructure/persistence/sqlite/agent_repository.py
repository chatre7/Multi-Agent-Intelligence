"""
SQLite Agent Repository Implementation.

Persists Agent entities to SQLite database.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, List, Optional

import sqlite3

from src.domain.entities.agent import Agent
from src.domain.repositories.agent_repository import IAgentRepository
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


class SqliteAgentRepository(IAgentRepository):
    """SQLite implementation of Agent repository."""

    def __init__(self, db_path: str = "data/agent_system.db"):
        """
        Initialize repository.

        Parameters
        ----------
        db_path : str
            Path to SQLite database file.
        """
        self.db_path = db_path
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                domain_id TEXT NOT NULL,
                description TEXT,
                version TEXT NOT NULL,
                state TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                model_name TEXT NOT NULL,
                temperature REAL,
                max_tokens INTEGER,
                timeout_seconds REAL,
                priority INTEGER DEFAULT 0,
                author TEXT,
                capabilities TEXT,
                tools TEXT,
                keywords TEXT,
                test_results TEXT,
                performance_metrics TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_domain ON agents(domain_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_state ON agents(state)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at)"
        )

        conn.commit()
        conn.close()

    def _agent_to_row(self, agent: Agent) -> dict[str, Any]:
        """Convert Agent to database row."""
        return {
            "id": agent.id,
            "name": agent.name,
            "domain_id": agent.domain_id,
            "description": agent.description,
            "version": str(agent.version),
            "state": agent.state.value,
            "system_prompt": agent.system_prompt,
            "model_name": agent.model_name,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "timeout_seconds": agent.timeout_seconds,
            "priority": agent.priority,
            "author": agent.author,
            "capabilities": json.dumps(agent.capabilities),
            "tools": json.dumps(agent.tools),
            "keywords": json.dumps(agent.keywords),
            "test_results": json.dumps(agent.test_results),
            "performance_metrics": json.dumps(agent.performance_metrics),
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
        }

    def _row_to_agent(self, row: sqlite3.Row) -> Agent:
        """Convert database row to Agent."""
        return Agent(
            id=row["id"],
            name=row["name"],
            domain_id=row["domain_id"],
            description=row["description"] or "",
            version=SemanticVersion.from_string(row["version"]),
            state=AgentState.from_string(row["state"]),
            system_prompt=row["system_prompt"],
            capabilities=json.loads(row["capabilities"] or "[]"),
            tools=json.loads(row["tools"] or "[]"),
            model_name=row["model_name"],
            temperature=row["temperature"] or 0.0,
            max_tokens=row["max_tokens"] or 4096,
            timeout_seconds=row["timeout_seconds"] or 120.0,
            keywords=json.loads(row["keywords"] or "[]"),
            priority=row["priority"] or 0,
            author=row["author"] or "system",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            test_results=json.loads(row["test_results"] or "{}"),
            performance_metrics=json.loads(row["performance_metrics"] or "{}"),
        )

    async def save(self, agent: Agent) -> Agent:
        """Save agent to database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        row = self._agent_to_row(agent)

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO agents VALUES (
                    :id, :name, :domain_id, :description, :version, :state,
                    :system_prompt, :model_name, :temperature, :max_tokens,
                    :timeout_seconds, :priority, :author, :capabilities,
                    :tools, :keywords, :test_results, :performance_metrics,
                    :created_at, :updated_at
                )
                """,
                row,
            )
            conn.commit()
            return agent
        finally:
            conn.close()

    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find agent by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            return self._row_to_agent(row) if row else None
        finally:
            conn.close()

    async def find_by_name(self, name: str) -> Optional[Agent]:
        """Find agent by name."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM agents WHERE name = ?", (name,))
            row = cursor.fetchone()
            return self._row_to_agent(row) if row else None
        finally:
            conn.close()

    async def find_by_domain(self, domain_id: str) -> List[Agent]:
        """Find agents in a domain."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM agents WHERE domain_id = ? ORDER BY priority ASC, name ASC",
                (domain_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_agent(row) for row in rows]
        finally:
            conn.close()

    async def find_by_state(self, state: AgentState) -> List[Agent]:
        """Find agents by state."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM agents WHERE state = ? ORDER BY updated_at DESC",
                (state.value,),
            )
            rows = cursor.fetchall()
            return [self._row_to_agent(row) for row in rows]
        finally:
            conn.close()

    async def find_all(self) -> List[Agent]:
        """Get all agents."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM agents ORDER BY domain_id, name")
            rows = cursor.fetchall()
            return [self._row_to_agent(row) for row in rows]
        finally:
            conn.close()

    async def delete(self, agent_id: str) -> bool:
        """Delete agent by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def find_by_keywords(self, keywords: List[str]) -> List[Agent]:
        """Find agents matching keywords."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get all agents and score them
            cursor.execute(
                "SELECT * FROM agents WHERE state = ? ORDER BY priority ASC",
                (AgentState.PRODUCTION.value,),
            )
            rows = cursor.fetchall()

            agents = []
            scores = []

            for row in rows:
                agent = self._row_to_agent(row)
                confidence = agent.can_handle("", keywords)
                if confidence > 0:
                    agents.append(agent)
                    scores.append(confidence)

            # Sort by confidence (highest first)
            sorted_agents = [
                x for _, x in sorted(zip(scores, agents), reverse=True)
            ]
            return sorted_agents
        finally:
            conn.close()

    async def find_active(self) -> List[Agent]:
        """Get all active agents."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            active_states = [
                AgentState.DEVELOPMENT.value,
                AgentState.TESTING.value,
                AgentState.PRODUCTION.value,
            ]

            placeholders = ",".join("?" * len(active_states))
            cursor.execute(
                f"SELECT * FROM agents WHERE state IN ({placeholders}) ORDER BY domain_id, name",
                active_states,
            )
            rows = cursor.fetchall()
            return [self._row_to_agent(row) for row in rows]
        finally:
            conn.close()
