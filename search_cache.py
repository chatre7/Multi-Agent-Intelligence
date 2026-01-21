"""
Web Search Cache System

File-based cache with 24-hour TTL for search results to reduce API calls
and improve performance while maintaining data freshness.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib


class SearchCache:
    """File-based cache for web search results with 24-hour TTL"""

    def __init__(self, cache_file: str = "data/search_cache.json", ttl_hours: int = 24):
        self.cache_file = cache_file
        self.ttl_seconds = ttl_hours * 3600
        self.cache: Dict[str, Dict] = {}

        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        # Load existing cache
        self.load_cache()

    def load_cache(self):
        """Load cache from disk and clean expired entries"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Clean expired entries
                current_time = datetime.utcnow().timestamp()
                self.cache = {
                    k: v
                    for k, v in data.items()
                    if current_time - v["timestamp"] < self.ttl_seconds
                }
            else:
                self.cache = {}
        except (json.JSONDecodeError, KeyError):
            # Corrupted cache, start fresh
            self.cache = {}

    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save search cache: {e}")

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
        if key in self.cache:
            entry = self.cache[key]
            current_time = datetime.utcnow().timestamp()

            if current_time - entry["timestamp"] < self.ttl_seconds:
                return entry["result"]
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.save_cache()

        return None

    def set(self, key: str, result: Dict[str, Any]):
        """Cache search result with timestamp"""
        self.cache[key] = {"timestamp": datetime.utcnow().timestamp(), "result": result}
        self.save_cache()

    def clear_expired(self):
        """Manually clear expired entries"""
        current_time = datetime.utcnow().timestamp()
        expired_keys = [
            k
            for k, v in self.cache.items()
            if current_time - v["timestamp"] >= self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.save_cache()
            print(f"Cleared {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        current_time = datetime.utcnow().timestamp()

        valid_entries = sum(
            1
            for v in self.cache.values()
            if current_time - v["timestamp"] < self.ttl_seconds
        )

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_file": self.cache_file,
            "ttl_hours": self.ttl_seconds / 3600,
        }


# Global cache instance
_search_cache = None


def get_search_cache() -> SearchCache:
    """Get or create the global search cache instance"""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache()
    return _search_cache
