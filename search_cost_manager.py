"""
Search Cost Manager

Manages search API costs, budget limits, and usage tracking
with notifications when approaching limits.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from search_config import SEARCH_CONFIG

logger = logging.getLogger(__name__)


class SearchCostManager:
    """Manages search API costs and budget enforcement"""

    def __init__(self, budget_file: str = "data/search_budget.json"):
        self.budget_file = budget_file
        self.daily_budget = SEARCH_CONFIG["daily_budget"]
        self.usage_today = 0.0
        self.last_reset_date = None

        # Ensure directory exists
        os.makedirs(os.path.dirname(budget_file), exist_ok=True)

        # Load existing budget data
        self.load_budget_data()

    def load_budget_data(self):
        """Load budget and usage data from disk"""
        try:
            if os.path.exists(self.budget_file):
                with open(self.budget_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.usage_today = data.get("usage_today", 0.0)
                    self.last_reset_date = data.get("last_reset_date")
            else:
                self.reset_daily_budget()
        except (json.JSONDecodeError, KeyError):
            # Corrupted data, reset
            self.reset_daily_budget()

    def save_budget_data(self):
        """Save budget and usage data to disk"""
        try:
            data = {
                "usage_today": self.usage_today,
                "last_reset_date": self.last_reset_date,
                "daily_budget": self.daily_budget,
            }
            with open(self.budget_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save budget data: {e}")

    def reset_daily_budget(self):
        """Reset daily usage counters"""
        self.usage_today = 0.0
        self.last_reset_date = datetime.utcnow().date().isoformat()
        self.save_budget_data()
        logger.info(f"🔄 Daily search budget reset: $0/${self.daily_budget}")

    def check_daily_reset(self):
        """Check if we need to reset daily counters"""
        today = datetime.utcnow().date().isoformat()

        if self.last_reset_date != today:
            self.reset_daily_budget()

    def check_budget(self) -> bool:
        """Check if we're within daily budget"""
        self.check_daily_reset()
        return self.usage_today < self.daily_budget

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        self.check_daily_reset()

        usage_percent = (
            (self.usage_today / self.daily_budget) * 100 if self.daily_budget > 0 else 0
        )

        return {
            "usage_today": self.usage_today,
            "daily_budget": self.daily_budget,
            "remaining": self.daily_budget - self.usage_today,
            "usage_percent": usage_percent,
            "within_budget": self.usage_today < self.daily_budget,
        }

    def track_cost(self, query: str, provider: str, result_count: int):
        """Track search API cost"""
        self.check_daily_reset()

        cost_per_query = SEARCH_CONFIG["cost_per_query"]
        total_cost = cost_per_query * result_count

        self.usage_today += total_cost
        self.save_budget_data()

        # Log the transaction
        logger.info(
            f"💰 Search cost: ${total_cost:.4f} (query: '{query[:50]}...', results: {result_count})"
        )

        # Send notifications based on usage thresholds
        self.send_budget_notifications()

        return total_cost

    def send_budget_notifications(self):
        """Send notifications when approaching budget limits"""
        status = self.get_budget_status()
        usage_percent = status["usage_percent"]

        if usage_percent >= 90:
            logger.error(
                f"🚨 CRITICAL: Search budget {usage_percent:.1f}% used (${self.usage_today:.2f}/${self.daily_budget})"
            )
            # In a real system, this could send emails/Slack notifications

        elif usage_percent >= 75:
            logger.warning(
                f"⚠️ WARNING: Search budget {usage_percent:.1f}% used (${self.usage_today:.2f}/${self.daily_budget})"
            )

        elif usage_percent >= 50:
            logger.info(
                f"ℹ️ INFO: Search budget {usage_percent:.1f}% used (${self.usage_today:.2f}/${self.daily_budget})"
            )

    def can_perform_search(self, user_role: str, user_id: str) -> tuple[bool, str]:
        """
        Check if a user can perform a search based on permissions and budget

        Returns:
            tuple: (can_search, reason_if_denied)
        """
        # Check role permissions
        role_config = SEARCH_CONFIG["permissions"].get(user_role, {"enabled": False})
        if not role_config["enabled"]:
            return (
                False,
                f"❌ Access denied: Role '{user_role}' does not have search permissions",
            )

        # Check budget
        if not self.check_budget():
            return (
                False,
                f"❌ Budget exceeded: Daily limit of ${self.daily_budget} reached",
            )

        # Check individual user limits (if implemented)
        # For now, rely on role-based limits

        return True, "✅ Search permitted"


# Global cost manager instance
_search_cost_manager = None


def get_search_cost_manager() -> SearchCostManager:
    """Get or create the global search cost manager instance"""
    global _search_cost_manager
    if _search_cost_manager is None:
        _search_cost_manager = SearchCostManager()
    return _search_cost_manager
