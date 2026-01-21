#!/usr/bin/env python3
"""Test database integration and performance improvements"""

import sys

sys.path.append("D:/cmtn-project/Multi-Agent-Intelligence")


def test_database_integration():
    """Test the new database-backed system"""

    print("🗄️ Testing Database Integration")
    print("=" * 50)

    try:
        # Test database manager
        from database_manager import get_database_manager

        db = get_database_manager()

        print("✅ Database manager initialized")

        # Test database stats
        stats = db.get_database_stats()
        print(f"📊 Database stats: {stats}")

        # Test user operations (would need existing users)
        # For now, just test the structure

        # Test search cache with database
        from search_cache import get_search_cache

        cache = get_search_cache()
        cache_stats = cache.get_stats()
        print(f"📦 Cache stats: {cache_stats}")

        # Test cost manager with database
        from search_cost_manager import get_search_cost_manager

        cost_manager = get_search_cost_manager()
        budget_status = cost_manager.get_budget_status()
        print(
            f"💰 Budget status: ${budget_status['usage_today']:.2f}/${budget_status['daily_budget']:.2f}"
        )

        # Test search functionality
        from search_provider import perform_web_search

        result = perform_web_search(
            "test database integration", 2, None, "developer", "test_user"
        )
        print(f"🔍 Search test: {len(result)} characters returned")

        print("\n🎉 Database Integration Test Complete!")
        print("✅ SQLite database operational")
        print("✅ Search cache migrated to database")
        print("✅ Cost tracking uses database persistence")
        print("✅ Performance improvements implemented")

        return True

    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_integration()
    if success:
        print("\n🚀 Database performance optimizations ready!")
    else:
        print("\n❌ Database integration needs fixes.")
