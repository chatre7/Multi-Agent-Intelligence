#!/usr/bin/env python3
"""Quick test of budget management system"""

from search_cost_manager import get_search_cost_manager


def test_budget_system():
    manager = get_search_cost_manager()
    status = manager.get_budget_status()

    print("💰 Budget Management Status:")
    print(f"  - Daily budget: ${status['daily_budget']:.2f}")
    print(f"  - Used today: ${status['usage_today']:.2f}")
    print(f"  - Remaining: ${status['remaining']:.2f}")
    print(f"  - Usage %: {status['usage_percent']:.1f}%")
    print(
        f"  - Status: {'✅ Within budget' if status['within_budget'] else '❌ Budget exceeded'}"
    )

    # Test permission checking
    can_search, reason = manager.can_perform_search("developer", "test_user")
    print("\n🔐 Permission Test (developer role):")
    print(f"  - Can search: {can_search}")
    print(f"  - Reason: {reason}")


if __name__ == "__main__":
    test_budget_system()
