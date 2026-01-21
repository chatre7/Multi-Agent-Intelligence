"""
Enhanced Database Manager for Multi-Agent Intelligence System

Upgrades from JSON-based storage to SQLite for better performance,
concurrency, and data integrity in production environments.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import threading


class DatabaseManager:
    """SQLite-based database manager for the multi-agent system"""

    def __init__(self, db_path: str = "data/agent_system.db"):
        self.db_path = db_path
        self._local = threading.local()  # Thread-local storage for connections
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Agent conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    message_type TEXT NOT NULL,  -- human, ai, system, tool
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for conversations table
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_thread_agent ON conversations (thread_id, agent_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations (created_at)"
            )

            # Agent performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration_ms INTEGER,
                    token_count INTEGER,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for agent_metrics
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_operation ON agent_metrics (agent_name, operation)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_created_at ON agent_metrics (created_at)"
            )

            # Search cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    cache_key TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    domain TEXT,
                    num_results INTEGER DEFAULT 5,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)

            # Create indexes for search_cache
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_cache_last_accessed ON search_cache (last_accessed)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_cache_query_domain ON search_cache (query, domain)"
            )

            # Search cost tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    result_count INTEGER,
                    cost_usd REAL DEFAULT 0.0,
                    user_id TEXT,
                    user_role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for search_costs
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_costs_date ON search_costs (DATE(created_at))"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_costs_user ON search_costs (user_id)"
            )

            # System configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert default configuration
            self._insert_default_config(cursor)

            conn.commit()

    def _insert_default_config(self, cursor):
        """Insert default system configuration"""
        default_config = {
            "system_version": "1.0.0",
            "max_conversation_length": "100",
            "search_daily_budget": "5.0",
            "cache_ttl_hours": "24",
            "max_concurrent_agents": "10",
            "enable_performance_monitoring": "true",
            "log_level": "INFO",
        }

        for key, value in default_config.items():
            cursor.execute(
                """
                INSERT OR IGNORE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
            """,
                (key, value, f"Default {key.replace('_', ' ')}"),
            )

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, "connection"):
            # Create connection with proper settings for concurrency
            self._local.connection = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")  # 10MB cache

        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise e

    # User Management Methods
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            user_id = user_data.get("id") or str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    user_data["username"],
                    user_data["email"],
                    user_data["password_hash"],
                    user_data.get("role", "user"),
                    user_data.get("is_active", True),
                    now,
                    now,
                ),
            )

            conn.commit()
            return self.get_user(user_id)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def update_user(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            set_parts = []
            values = []

            for key, value in update_data.items():
                if key in ["username", "email", "password_hash", "role", "is_active"]:
                    set_parts.append(f"{key} = ?")
                    values.append(value)

            if not set_parts:
                return self.get_user(user_id)

            set_parts.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())

            query = f"UPDATE users SET {', '.join(set_parts)} WHERE id = ?"
            values.append(user_id)

            cursor.execute(query, values)
            conn.commit()

            return self.get_user(user_id)

    def list_users(
        self, role_filter: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List users with optional filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM users"
            params = []

            if role_filter:
                query += " WHERE role = ?"
                params.append(role_filter)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # Conversation Management Methods
    def save_message(
        self,
        thread_id: str,
        agent_name: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a conversation message"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            message_id = str(uuid.uuid4())
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT INTO conversations (id, thread_id, agent_name, message_type, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    thread_id,
                    agent_name,
                    message_type,
                    content,
                    metadata_json,
                ),
            )

            conn.commit()
            return message_id

    def get_conversation_history(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a thread"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM conversations
                WHERE thread_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """,
                (thread_id, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_agent_conversation_stats(
        self, agent_name: str, days: int = 7
    ) -> Dict[str, Any]:
        """Get conversation statistics for an agent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculate date threshold
            threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT thread_id) as unique_threads,
                    message_type,
                    AVG(LENGTH(content)) as avg_content_length
                FROM conversations
                WHERE agent_name = ? AND created_at >= ?
                GROUP BY message_type
            """,
                (agent_name, threshold_date),
            )

            stats = {}
            for row in cursor.fetchall():
                stats[row["message_type"]] = dict(row)

            return stats

    # Performance Metrics Methods
    def record_agent_metric(
        self,
        agent_name: str,
        operation: str,
        duration_ms: int,
        token_count: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record agent performance metric"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT INTO agent_metrics
                (agent_name, operation, duration_ms, token_count, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent_name,
                    operation,
                    duration_ms,
                    token_count,
                    success,
                    error_message,
                    metadata_json,
                ),
            )

            conn.commit()

    def get_agent_performance_stats(
        self, agent_name: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """Get agent performance statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            query = """
                SELECT
                    agent_name,
                    operation,
                    COUNT(*) as operation_count,
                    AVG(duration_ms) as avg_duration_ms,
                    MIN(duration_ms) as min_duration_ms,
                    MAX(duration_ms) as max_duration_ms,
                    AVG(token_count) as avg_tokens,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM agent_metrics
                WHERE created_at >= ?
            """

            params = [threshold_date]

            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            query += " GROUP BY agent_name, operation ORDER BY agent_name, operation_count DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # Search Cache Methods
    def get_cached_search(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT result_data, created_at FROM search_cache
                WHERE cache_key = ?
            """,
                (cache_key,),
            )

            row = cursor.fetchone()
            if row:
                # Update last accessed time
                cursor.execute(
                    """
                    UPDATE search_cache
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE cache_key = ?
                """,
                    (cache_key,),
                )
                conn.commit()

                return {
                    "result": json.loads(row["result_data"]),
                    "created_at": row["created_at"],
                }
            return None

    def set_cached_search(
        self,
        cache_key: str,
        query: str,
        domain: Optional[str],
        num_results: int,
        result_data: Dict[str, Any],
    ):
        """Cache search result"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            result_json = json.dumps(result_data)

            cursor.execute(
                """
                INSERT OR REPLACE INTO search_cache
                (cache_key, query, domain, num_results, result_data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (cache_key, query, domain, num_results, result_json),
            )

            conn.commit()

    def cleanup_expired_cache(self, max_age_hours: int = 24):
        """Clean up expired cache entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            threshold_time = (
                datetime.utcnow() - timedelta(hours=max_age_hours)
            ).isoformat()

            cursor.execute(
                "DELETE FROM search_cache WHERE created_at < ?", (threshold_time,)
            )
            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

    # Search Cost Methods
    def record_search_cost(
        self,
        query: str,
        provider: str,
        result_count: int,
        cost_usd: float,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ):
        """Record search API cost"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO search_costs
                (query, provider, result_count, cost_usd, user_id, user_role)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (query, provider, result_count, cost_usd, user_id, user_role),
            )

            conn.commit()

    def get_search_cost_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get search cost statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                SELECT
                    DATE(created_at) as date,
                    provider,
                    COUNT(*) as query_count,
                    SUM(result_count) as total_results,
                    SUM(cost_usd) as total_cost
                FROM search_costs
                WHERE created_at >= ?
                GROUP BY DATE(created_at), provider
                ORDER BY date DESC, total_cost DESC
            """,
                (threshold_date,),
            )

            return [dict(row) for row in cursor.fetchall()]

    # Configuration Methods
    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_config(self, key: str, value: str, description: Optional[str] = None):
        """Set configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO system_config (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value, description or f"Configuration for {key}"),
            )

            conn.commit()

    # Migration and Maintenance Methods
    def migrate_from_json(self, json_data: Dict[str, Any]):
        """Migrate data from JSON files to database"""
        # This would be used to migrate existing users.json, etc.
        # Implementation would depend on the specific JSON structure
        pass

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Table sizes
            tables = [
                "users",
                "conversations",
                "agent_metrics",
                "search_cache",
                "search_costs",
            ]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()["count"]

            # Database file size
            try:
                stats["db_size_mb"] = os.path.getsize(self.db_path) / (1024 * 1024)
            except OSError:
                stats["db_size_mb"] = 0

            return stats

    def optimize_database(self):
        """Optimize database performance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Rebuild indexes
            cursor.execute("REINDEX")

            # Vacuum database
            cursor.execute("VACUUM")

            # Analyze tables for query optimization
            cursor.execute("ANALYZE")

            conn.commit()


# Global database instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
