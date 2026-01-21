"""
Search Cost Manager

Manages search API costs, budget limits, and usage tracking
with database persistence and notifications when approaching limits.
"""

from typing import Dict, Any, Optional
import logging

from search_config import SEARCH_CONFIG
from database_manager import get_database_manager

logger = logging.getLogger(__name__)


class SearchCostManager:
    """Manages search API costs and budget enforcement with database persistence"""

    def __init__(self):
        self.db = get_database_manager()
        self.daily_budget = float(SEARCH_CONFIG["daily_budget"])
        self._load_budget_data()

    def _load_budget_data(self):
        """Load budget data from database"""
        # Get today's usage from database
        cost_stats = self.db.get_search_cost_stats(days=1)
        today_usage = sum(stat.get("total_cost", 0) for stat in cost_stats)
        self.usage_today = today_usage

    def check_budget(self) -> bool:
        """Check if we're within daily budget"""
        # Always reload budget data to ensure accuracy
        self._load_budget_data()
        return self.usage_today < self.daily_budget

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        self._load_budget_data()

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

    def track_cost(
        self,
        query: str,
        provider: str,
        result_count: int,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> float:
        """Track search API cost in database"""
        cost_per_query = SEARCH_CONFIG["cost_per_query"]
        total_cost = cost_per_query * result_count

        # Record in database
        self.db.record_search_cost(
            query, provider, result_count, total_cost, user_id, user_role
        )

        # Update local cache
        self.usage_today += total_cost

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

        return True, "✅ Search permitted"

    def get_cost_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive cost analytics"""
        return {
            "budget_status": self.get_budget_status(),
            "cost_history": self.db.get_search_cost_stats(days),
            "total_cost_period": sum(
                stat.get("total_cost", 0)
                for stat in self.db.get_search_cost_stats(days)
            ),
        }


# Global cost manager instance
_search_cost_manager = None


def get_search_cost_manager() -> SearchCostManager:
    """Get or create the global search cost manager instance"""
    global _search_cost_manager
    if _search_cost_manager is None:
        _search_cost_manager = SearchCostManager()
    return _search_cost_manager
