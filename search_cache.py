"""
Web Search Cache System

Database-backed cache for web search results with TTL management
for improved performance and reduced API costs.
"""

import hashlib
from typing import Optional, Dict, Any
from database_manager import get_database_manager


class SearchCache:
    """Database-backed cache for web search results with TTL"""

    def __init__(self, ttl_hours: int = 24):
        self.ttl_hours = ttl_hours
        self.db = get_database_manager()

    def get_cache_key(
        self, query: str, domain: Optional[str] = None, num_results: int = 5
    ) -> str:
        """Generate consistent cache key"""
        key_components = [query, str(num_results)]
        if domain:
            key_components.insert(0, domain)
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid"""
        cached = self.db.get_cached_search(key)
        return cached["result"] if cached else None

    def set(
        self,
        key: str,
        result: Dict[str, Any],
        query: str = "",
        domain: Optional[str] = None,
        num_results: int = 5,
    ):
        """Cache search result"""
        self.db.set_cached_search(key, query, domain, num_results, result)

    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        return self.db.cleanup_expired_cache(self.ttl_hours)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics from database"""
        db_stats = self.db.get_database_stats()
        return {
            "cache_entries": db_stats.get("search_cache_count", 0),
            "ttl_hours": self.ttl_hours,
            "storage_type": "SQLite Database",
        }


# Global cache instance
_search_cache = None


def get_search_cache() -> SearchCache:
    """Get or create the global search cache instance"""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache()
    return _search_cache
