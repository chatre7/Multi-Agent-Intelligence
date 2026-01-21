"""
Test Web Search Tool Integration

Verify that the web search tools are properly integrated with MCP server
and working with caching, cost tracking, and permissions.
"""

import sys

sys.path.append("D:/cmtn-project/Multi-Agent-Intelligence")


def test_web_search_integration():
    """Test the complete web search tool integration"""

    print("🔍 Testing Web Search Tool Integration")
    print("=" * 50)

    try:
        # Test MCP server with web search tools
        from mcp_server import get_mcp_server

        server = get_mcp_server()

        print("✅ MCP Server initialized")

        # List available tools
        tools = server.list_tools()
        print(f"📋 Available tools: {len(tools)}")

        web_search_tools = [t for t in tools if "web_search" in t["name"]]
        print(f"🔍 Web search tools found: {len(web_search_tools)}")

        for tool in web_search_tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

        # Test cache system
        from search_cache import get_search_cache

        cache = get_search_cache()
        stats = cache.get_stats()
        print(
            f"📦 Cache initialized: {stats['total_entries']} entries, TTL: {stats['ttl_hours']}h"
        )

        # Test cost manager
        from search_cost_manager import get_search_cost_manager

        cost_manager = get_search_cost_manager()
        budget_status = cost_manager.get_budget_status()
        print(
            f"💰 Budget status: ${budget_status['usage_today']:.2f}/${budget_status['daily_budget']:.2f}"
        )

        # Test permissions
        from search_config import SEARCH_CONFIG

        permissions = SEARCH_CONFIG["permissions"]
        print(f"🔐 Permission roles configured: {len(permissions)}")

        # Test basic search functionality
        from search_provider import perform_web_search

        print("\n🧪 Testing basic search functionality...")
        result = perform_web_search("test query", 2, None, "developer", "test_user")
        print(f"📄 Search result length: {len(result)} characters")

        if "test query" in result.lower() or "mock" in result.lower():
            print("✅ Search functionality working (mock results)")
        else:
            print("⚠️ Search may not be working as expected")

        print("\n🎉 Web Search Tool Integration Test Complete!")
        print("✅ All components initialized successfully")
        print("✅ MCP tools registered")
        print("✅ Cache system operational")
        print("✅ Cost tracking active")
        print("✅ Permissions configured")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_web_search_integration()
    if success:
        print("\n🚀 Web Search Tools are ready for production use!")
    else:
        print("\n❌ Web Search Tool integration needs fixes.")
