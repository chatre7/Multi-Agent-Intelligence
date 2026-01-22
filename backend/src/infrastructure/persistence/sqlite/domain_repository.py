"""SQLite Domain Repository Implementation."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, List, Optional

from src.domain.entities.domain_config import DomainConfig, RoutingRule
from src.domain.repositories.domain_repository import IDomainRepository


class SqliteDomainRepository(IDomainRepository):
    """SQLite implementation of Domain repository."""

    def __init__(self, db_path: str = "data/agent_system.db"):
        self.db_path = db_path
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS domains (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                workflow_type TEXT,
                max_iterations INTEGER,
                version TEXT,
                is_active BOOLEAN DEFAULT 1,
                agents TEXT,
                default_agent TEXT,
                fallback_agent TEXT,
                routing_rules TEXT,
                allowed_roles TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_domains_active ON domains(is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_domains_created ON domains(created_at)"
        )

        conn.commit()
        conn.close()

    def _domain_to_row(self, domain: DomainConfig) -> dict[str, Any]:
        return {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description,
            "workflow_type": domain.workflow_type,
            "max_iterations": domain.max_iterations,
            "version": domain.version,
            "is_active": domain.is_active,
            "agents": json.dumps(domain.agents),
            "default_agent": domain.default_agent,
            "fallback_agent": domain.fallback_agent,
            "routing_rules": json.dumps([r.to_dict() for r in domain.routing_rules]),
            "allowed_roles": json.dumps(domain.allowed_roles),
            "metadata": json.dumps(domain.metadata),
            "created_at": domain.created_at.isoformat(),
            "updated_at": domain.updated_at.isoformat(),
        }

    def _row_to_domain(self, row: sqlite3.Row) -> DomainConfig:
        routing_rules = [
            RoutingRule.from_dict(r) for r in json.loads(row["routing_rules"] or "[]")
        ]

        return DomainConfig(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            agents=json.loads(row["agents"] or "[]"),
            default_agent=row["default_agent"] or "",
            workflow_type=row["workflow_type"] or "supervisor",
            max_iterations=row["max_iterations"] or 10,
            routing_rules=routing_rules,
            fallback_agent=row["fallback_agent"] or "",
            allowed_roles=json.loads(row["allowed_roles"] or "[]"),
            version=row["version"] or "1.0.0",
            is_active=bool(row["is_active"]),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    async def save(self, domain: DomainConfig) -> DomainConfig:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            row = self._domain_to_row(domain)
            cursor.execute(
                """
                INSERT OR REPLACE INTO domains VALUES (
                    :id, :name, :description, :workflow_type, :max_iterations,
                    :version, :is_active, :agents, :default_agent, :fallback_agent,
                    :routing_rules, :allowed_roles, :metadata, :created_at, :updated_at
                )
                """,
                row,
            )
            conn.commit()
            return domain
        finally:
            conn.close()

    async def find_by_id(self, domain_id: str) -> Optional[DomainConfig]:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM domains WHERE id = ?", (domain_id,))
            row = cursor.fetchone()
            return self._row_to_domain(row) if row else None
        finally:
            conn.close()

    async def find_all(self) -> List[DomainConfig]:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM domains ORDER BY name")
            rows = cursor.fetchall()
            return [self._row_to_domain(row) for row in rows]
        finally:
            conn.close()

    async def delete(self, domain_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def find_active(self) -> List[DomainConfig]:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM domains WHERE is_active = 1 ORDER BY name")
            rows = cursor.fetchall()
            return [self._row_to_domain(row) for row in rows]
        finally:
            conn.close()

    async def exists(self, domain_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT 1 FROM domains WHERE id = ?", (domain_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
