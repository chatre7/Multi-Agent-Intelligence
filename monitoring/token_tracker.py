"""Token Consumption and Cost Tracker.

Tracks token usage across the multi-agent system with cost estimation.
Implements Microsoft's operational resilience guidelines for token monitoring.
"""

import os
import json
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler


@dataclass
class TokenCosts:
    """Token pricing information per 1K tokens."""

    model_name: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    currency: str = "USD"


@dataclass
class TokenRecord:
    """Single token usage record."""

    timestamp: float
    agent_name: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class TokenTracker(BaseCallbackHandler):
    """LangChain callback handler for tracking token usage and costs.

    Provides:
    - Real-time token usage tracking
    - Cost estimation per model
    - Usage limits and alerts
    - Historical usage data
    - Export functionality
    """

    DEFAULT_COSTS = {
        "gpt-4": TokenCosts("gpt-4", 0.03, 0.06),
        "gpt-4-turbo": TokenCosts("gpt-4-turbo", 0.01, 0.03),
        "gpt-4o": TokenCosts("gpt-4o", 0.005, 0.015),
        "gpt-4o-mini": TokenCosts("gpt-4o-mini", 0.00015, 0.0006),
        "gpt-3.5-turbo": TokenCosts("gpt-3.5-turbo", 0.0015, 0.002),
        "gpt-oss:120b-cloud": TokenCosts("gpt-oss:120b-cloud", 0.0001, 0.0001),
        "claude-3-opus": TokenCosts("claude-3-opus", 0.015, 0.075),
        "claude-3-sonnet": TokenCosts("claude-3-sonnet", 0.003, 0.015),
        "claude-3-haiku": TokenCosts("claude-3-haiku", 0.00025, 0.00125),
    }

    def __init__(
        self,
        model_costs: Optional[Dict[str, TokenCosts]] = None,
        daily_token_limit: Optional[int] = None,
        daily_cost_limit: Optional[float] = None,
        storage_path: Optional[str] = None,
    ):
        super().__init__()

        self._model_costs = model_costs or self.DEFAULT_COSTS.copy()
        self._daily_token_limit = daily_token_limit
        self._daily_cost_limit = daily_cost_limit
        self._storage_path = storage_path or "./token_usage.json"

        self._records: List[TokenRecord] = []
        self._current_session_tokens: Dict[str, int] = {}
        self._current_session_costs: Dict[str, float] = {}

        self._on_usage_callbacks: List[Callable] = []
        self._on_limit_callbacks: List[Callable] = []

        self._load_history()

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated."""
        pass

    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating response."""
        try:
            llm_output = (
                response.generations[0]
                if hasattr(response, "generations") and response.generations
                else response
            )

            input_tokens = 0
            output_tokens = 0
            model_name = kwargs.get("invocation_params", {}).get("model", "unknown")

            if hasattr(llm_output, "token_usage") and llm_output.token_usage:
                usage = llm_output.token_usage
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
            elif hasattr(response, "llm_output") and hasattr(
                response.llm_output, "token_usage"
            ):
                usage = response.llm_output.token_usage
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
            else:
                input_tokens = kwargs.get("prompt_tokens", 0)
                output_tokens = kwargs.get("completion_tokens", 0)

            total_tokens = input_tokens + output_tokens
            estimated_cost = self._calculate_cost(
                model_name, input_tokens, output_tokens
            )

            record = TokenRecord(
                timestamp=time.time(),
                agent_name=kwargs.get("tags", ["unknown"])[0]
                if kwargs.get("tags")
                else "unknown",
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
            )

            self._records.append(record)
            self._update_session_stats(model_name, total_tokens, estimated_cost)

            self._notify_callbacks(record)
            self._check_limits(model_name)

            self._save_history()

        except Exception as e:
            print(f"Token tracker error: {e}")

    def _calculate_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost for token usage.

        Parameters
        ----------
        model_name : str
            Name of the model.
        input_tokens : int
            Number of input tokens.
        output_tokens : int
            Number of output tokens.

        Returns
        -------
        float
            Estimated cost in USD.
        """
        costs = self._model_costs.get(model_name)
        if not costs:
            return 0.0

        input_cost = (input_tokens / 1000) * costs.input_cost_per_1k
        output_cost = (output_tokens / 1000) * costs.output_cost_per_1k

        return input_cost + output_cost

    def _update_session_stats(self, model_name: str, tokens: int, cost: float) -> None:
        """Update session statistics.

        Parameters
        ----------
        model_name : str
            Name of the model.
        tokens : int
            Total tokens used.
        cost : float
            Cost of tokens.
        """
        self._current_session_tokens[model_name] = (
            self._current_session_tokens.get(model_name, 0) + tokens
        )
        self._current_session_costs[model_name] = (
            self._current_session_costs.get(model_name, 0.0) + cost
        )

    def _check_limits(self, model_name: str) -> None:
        """Check if usage limits are exceeded.

        Parameters
        ----------
        model_name : str
            Name of the model.
        """
        if self._daily_token_limit:
            daily_tokens = self._get_daily_tokens(model_name)
            if daily_tokens >= self._daily_token_limit:
                self._notify_limit_callbacks("token_limit", model_name, daily_tokens)

        if self._daily_cost_limit:
            daily_cost = self._get_daily_cost(model_name)
            if daily_cost >= self._daily_cost_limit:
                self._notify_limit_callbacks("cost_limit", model_name, daily_cost)

    def _notify_callbacks(self, record: TokenRecord) -> None:
        """Notify all registered callbacks of usage.

        Parameters
        ----------
        record : TokenRecord
            Token usage record.
        """
        for callback in self._on_usage_callbacks:
            try:
                callback(record)
            except Exception as e:
                print(f"Callback error: {e}")

    def _notify_limit_callbacks(
        self, limit_type: str, model_name: str, value: float
    ) -> None:
        """Notify all registered callbacks of limit exceeded.

        Parameters
        ----------
        limit_type : str
            Type of limit (token_limit or cost_limit).
        model_name : str
            Name of the model.
        value : float
            Current value.
        """
        for callback in self._on_limit_callbacks:
            try:
                callback(limit_type, model_name, value)
            except Exception as e:
                print(f"Limit callback error: {e}")

    def register_usage_callback(self, callback: Callable[[TokenRecord], None]) -> None:
        """Register callback to be called on each token usage.

        Parameters
        ----------
        callback : Callable[[TokenRecord], None]
            Function to call with token record.
        """
        self._on_usage_callbacks.append(callback)

    def register_limit_callback(
        self, callback: Callable[[str, str, float], None]
    ) -> None:
        """Register callback to be called when limits are exceeded.

        Parameters
        ----------
        callback : Callable[[str, str, float], None]
            Function to call with limit type, model name, and value.
        """
        self._on_limit_callbacks.append(callback)

    def _load_history(self) -> None:
        """Load usage history from storage."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._records = [TokenRecord(**r) for r in data.get("records", [])]
        except Exception as e:
            print(f"Failed to load history: {e}")
            self._records = []

    def _save_history(self) -> None:
        """Save usage history to storage."""
        try:
            Path(self._storage_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "records": [r.to_dict() for r in self._records],
                "last_updated": datetime.now(UTC).isoformat(),
            }

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def get_session_summary(self) -> Dict[str, any]:
        """Get current session summary.

        Returns
        -------
        Dict[str, any]
            Session usage summary.
        """
        return {
            "total_tokens": sum(self._current_session_tokens.values()),
            "total_cost": sum(self._current_session_costs.values()),
            "by_model": {
                model: {
                    "tokens": tokens,
                    "cost": self._current_session_costs.get(model, 0.0),
                }
                for model, tokens in self._current_session_tokens.items()
            },
        }

    def get_daily_tokens(self, model_name: Optional[str] = None) -> Dict[str, int]:
        """Get daily token usage.

        Parameters
        ----------
        model_name : Optional[str]
            Filter by specific model.

        Returns
        -------
        Dict[str, int]
            Daily token usage per model.
        """
        today = datetime.now().date()
        midnight = datetime.combine(today, datetime.min.time()).timestamp()

        records = [r for r in self._records if r.timestamp >= midnight]

        if model_name:
            records = [r for r in records if r.model_name == model_name]

        return {
            "total": sum(r.total_tokens for r in records),
            "input": sum(r.input_tokens for r in records),
            "output": sum(r.output_tokens for r in records),
        }

    def _get_daily_tokens(self, model_name: Optional[str] = None) -> int:
        """Get daily token count.

        Parameters
        ----------
        model_name : Optional[str]
            Filter by specific model.

        Returns
        -------
        int
            Total tokens used today.
        """
        return self.get_daily_tokens(model_name)["total"]

    def get_daily_cost(self, model_name: Optional[str] = None) -> float:
        """Get daily cost.

        Parameters
        ----------
        model_name : Optional[str]
            Filter by specific model.

        Returns
        -------
        float
            Total cost today.
        """
        today = datetime.now().date()
        midnight = datetime.combine(today, datetime.min.time()).timestamp()

        records = [r for r in self._records if r.timestamp >= midnight]

        if model_name:
            records = [r for r in records if r.model_name == model_name]

        return sum(r.estimated_cost for r in records)

    def get_usage_by_agent(self, agent_name: str) -> Dict[str, any]:
        """Get usage statistics for a specific agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.

        Returns
        -------
        Dict[str, any]
            Usage statistics for agent.
        """
        records = [r for r in self._records if r.agent_name == agent_name]

        return {
            "agent": agent_name,
            "total_calls": len(records),
            "total_tokens": sum(r.total_tokens for r in records),
            "total_cost": sum(r.estimated_cost for r in records),
            "by_model": {
                model: {
                    "tokens": sum(r.total_tokens for r in model_records),
                    "cost": sum(r.estimated_cost for r in model_records),
                }
                for model in set(r.model_name for r in records)
                if (model_records := [r for r in records if r.model_name == model])
            },
        }

    def get_usage_history(self, hours: int = 24) -> List[TokenRecord]:
        """Get usage history for specified time period.

        Parameters
        ----------
        hours : int
            Number of hours to look back.

        Returns
        -------
        List[TokenRecord]
            Usage records within time period.
        """
        cutoff = time.time() - (hours * 3600)
        return [r for r in self._records if r.timestamp >= cutoff]

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """Export usage history to JSON file.

        Parameters
        ----------
        filepath : Optional[str]
            Path to save file. If None, generates filename.

        Returns
        -------
        str
            Path to exported file.
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"./token_usage_export_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self._records], f, indent=2)

        return filepath

    def reset_session(self) -> None:
        """Reset current session statistics."""
        self._current_session_tokens.clear()
        self._current_session_costs.clear()

    def set_model_cost(
        self, model_name: str, input_cost: float, output_cost: float
    ) -> None:
        """Update or add cost information for a model.

        Parameters
        ----------
        model_name : str
            Name of the model.
        input_cost : float
            Cost per 1K input tokens.
        output_cost : float
            Cost per 1K output tokens.
        """
        self._model_costs[model_name] = TokenCosts(model_name, input_cost, output_cost)


# Singleton instance
_tracker: Optional[TokenTracker] = None


def get_token_tracker(
    daily_token_limit: Optional[int] = None, daily_cost_limit: Optional[float] = None
) -> TokenTracker:
    """Get or create singleton token tracker instance.

    Parameters
    ----------
    daily_token_limit : Optional[int]
        Daily token usage limit.
    daily_cost_limit : Optional[float]
        Daily cost limit in USD.

    Returns
    -------
    TokenTracker
        The token tracker instance.
    """
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker(
            daily_token_limit=daily_token_limit, daily_cost_limit=daily_cost_limit
        )
    return _tracker


if __name__ == "__main__":
    tracker = TokenTracker(daily_cost_limit=1.0)

    def on_usage(record):
        print(
            f"Usage: {record.agent_name} - {record.total_tokens} tokens - ${record.estimated_cost:.6f}"
        )

    def on_limit(limit_type, model_name, value):
        print(f"⚠️ Limit exceeded: {limit_type} for {model_name} - {value}")

    tracker.register_usage_callback(on_usage)
    tracker.register_limit_callback(on_limit)

    print("Session summary:")
    print(json.dumps(tracker.get_session_summary(), indent=2))

    print("\nDaily tokens:")
    print(json.dumps(tracker.get_daily_tokens(), indent=2))

    print("\nDaily cost:")
    print(f"${tracker.get_daily_cost():.6f}")
