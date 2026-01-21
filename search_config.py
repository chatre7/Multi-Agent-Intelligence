"""
Web Search Tool Configuration

Configuration for web search functionality including providers,
budget limits, caching, and permissions.
"""

SEARCH_CONFIG = {
    "provider": "duckduckgo",  # Free, no API key required
    "rate_limit": 10,  # queries/minute per agent
    "daily_budget": 5.0,  # $5/day limit (for future paid providers)
    "cost_per_query": 0.0,  # DuckDuckGo is free
    "cache_ttl_hours": 24,  # 24-hour cache
    "fallback_providers": ["tavily", "serper"],  # For future expansion
    # RBAC permissions for search access
    "permissions": {
        "admin": {"enabled": True, "daily_limit": 100},
        "developer": {"enabled": True, "daily_limit": 50},
        "operator": {"enabled": True, "daily_limit": 20},
        "user": {"enabled": True, "daily_limit": 10},
        "agent": {"enabled": True, "daily_limit": 5},
        "guest": {"enabled": False, "daily_limit": 0},
    },
}
