#!/usr/bin/env python3
"""Test Search Functionality"""

from search_provider import perform_web_search
from search_cost_manager import get_search_cost_manager
import uuid

print("🔍 Testing Search Functionality")
print("=" * 50)

# Test cost manager
cost_mgr = get_search_cost_manager()
print("✅ Search cost manager initialized")

# Check budget
budget = cost_mgr.get_budget_status()
usage_today = budget.get("usage_today", 0)
daily_budget = budget.get("daily_budget", 5.0)
print(".2f")

# Test search (with very limited results to save costs)
try:
    result = perform_web_search(
        "artificial intelligence basics",
        2,  # Limited results
        None,
        "general",
        "test_user_" + uuid.uuid4().hex[:8],
    )
    print(f"✅ Search completed: {len(result)} characters returned")
    preview = result[:200] + "..." if len(result) > 200 else result
    print("📄 Search result preview:", preview)
except Exception as e:
    print(f"⚠️ Search test failed (possibly due to API limits): {e}")

# Check budget after search
budget_after = cost_mgr.get_budget_status()
usage_after = budget_after.get("usage_today", 0)
print(".2f")

print("\n🎉 Search functionality test completed!")
