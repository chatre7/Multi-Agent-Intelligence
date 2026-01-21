"""
Web Search Provider

DuckDuckGo-based web search implementation with result formatting
and error handling for the MCP tools.
"""

import logging
from typing import List, Dict, Optional

from search_cache import get_search_cache
from search_cost_manager import get_search_cost_manager

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result"""

    def __init__(
        self, title: str, url: str, snippet: str, domain: Optional[str] = None
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.domain = domain or self.extract_domain(url)

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return url

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for caching/serialization"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
        }


def search_duckduckgo(
    query: str, num_results: int = 5, domain_filter: Optional[str] = None
) -> List[SearchResult]:
    """
    Search using DuckDuckGo Instant Answer API

    Args:
        query: Search query
        num_results: Maximum number of results to return
        domain_filter: Optional domain to filter results (e.g., "docs.python.org")

    Returns:
        List of SearchResult objects
    """
    try:
        # Construct search query
        search_query = query
        if domain_filter:
            search_query = f"site:{domain_filter} {query}"

        # DuckDuckGo Instant Answer API
        # Note: This is a simplified implementation. In production, you might want to use
        # a more robust search API or handle DuckDuckGo's rate limiting better.

        # For demonstration, we'll simulate search results
        # In a real implementation, you would call the actual DuckDuckGo API
        results = _mock_duckduckgo_search(search_query, num_results)

        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_result = SearchResult(
                title=result.get("title", "No Title"),
                url=result.get("url", "#"),
                snippet=result.get("snippet", "No description available"),
            )
            search_results.append(search_result)

        return search_results[:num_results]

    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        # Return empty results on failure (graceful degradation)
        return []


def _mock_duckduckgo_search(query: str, num_results: int) -> List[Dict[str, str]]:
    """
    Mock DuckDuckGo search results for development/testing
    In production, replace with actual API calls
    """
    # This is a mock implementation for development
    # Replace with actual DuckDuckGo API integration

    mock_results = [
        {
            "title": f"Search results for: {query}",
            "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            "snippet": f"Find information about {query} from various sources on the web.",
        },
        {
            "title": f"{query} - Documentation",
            "url": f"https://docs.example.com/{query.replace(' ', '-').lower()}",
            "snippet": f"Official documentation and guides for {query}.",
        },
        {
            "title": f"{query} Tutorial",
            "url": f"https://tutorial.example.com/{query.replace(' ', '-').lower()}",
            "snippet": f"Step-by-step tutorial on how to use {query}.",
        },
        {
            "title": f"{query} Best Practices",
            "url": f"https://best-practices.example.com/{query.replace(' ', '-').lower()}",
            "snippet": f"Industry best practices and recommendations for {query}.",
        },
        {
            "title": f"{query} API Reference",
            "url": f"https://api.example.com/{query.replace(' ', '-').lower()}",
            "snippet": f"Complete API reference and examples for {query}.",
        },
    ]

    return mock_results[:num_results]


def format_search_results(results: List[SearchResult]) -> str:
    """
    Format search results for agent consumption

    Args:
        results: List of SearchResult objects

    Returns:
        Formatted string suitable for LLM consumption
    """
    if not results:
        return "🔍 No search results found. Proceeding with available knowledge."

    formatted = f"🔍 Found {len(results)} search results:\n\n"

    for i, result in enumerate(results, 1):
        formatted += f"**{i}. {result.title}**\n"
        formatted += f"   🔗 {result.url}\n"
        formatted += f"   📄 {result.snippet}\n\n"

    formatted += "💡 Use this information to inform your response. Focus on the most relevant results for the current task."

    return formatted


def perform_web_search(
    query: str,
    num_results: int = 5,
    domain_filter: Optional[str] = None,
    user_role: str = "user",
    user_id: str = "anonymous",
) -> str:
    """
    Main web search function with caching, cost tracking, and permissions

    Args:
        query: Search query
        num_results: Number of results to return
        domain_filter: Optional domain filter
        user_role: User's role for permission checking
        user_id: User ID for tracking

    Returns:
        Formatted search results or error message
    """
    cost_manager = get_search_cost_manager()
    cache = get_search_cache()

    # Check permissions and budget
    can_search, reason = cost_manager.can_perform_search(user_role, user_id)
    if not can_search:
        return reason

    # Check cache first
    cache_key = cache.get_cache_key(query, domain_filter, num_results)
    cached_result = cache.get(cache_key)

    if cached_result:
        return f"📋 [CACHED] {cached_result}"

    # Perform search
    try:
        results = search_duckduckgo(query, num_results, domain_filter)
        formatted_results = format_search_results(results)

        # Track costs (even though DuckDuckGo is free, for future paid providers)
        cost_manager.track_cost(query, "duckduckgo", len(results))

        # Cache the results
        cache.set(cache_key, formatted_results)

        return f"🔍 [LIVE] {formatted_results}"

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return "⚠️ Search temporarily unavailable. Proceeding with available knowledge."


def perform_domain_search(
    query: str,
    domain: str,
    num_results: int = 3,
    user_role: str = "user",
    user_id: str = "anonymous",
) -> str:
    """
    Search within a specific domain (e.g., documentation sites)

    Args:
        query: Search query
        domain: Domain to search within
        num_results: Number of results to return
        user_role: User's role for permissions
        user_id: User ID for tracking

    Returns:
        Formatted domain-specific search results
    """
    return perform_web_search(
        query=query,
        num_results=num_results,
        domain_filter=domain,
        user_role=user_role,
        user_id=user_id,
    )
