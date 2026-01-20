"""Metrics and Observability System.

Implements Prometheus metrics for multi-agent system monitoring.
Tracks token usage, agent performance, and system health metrics.
"""

import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    start_http_server,
    make_asgi_app,
)


@dataclass
class TokenUsage:
    """Token usage statistics for a single agent call."""

    agent_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_name: str
    timestamp: float = field(default_factory=time.time)


class AgentMetrics:
    """Metrics collection system for multi-agent architecture.

    Provides:
    - Token consumption tracking
    - Agent performance metrics
    - Request latency histograms
    - Error rate counters
    - System health gauges
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self._registry = registry or CollectorRegistry()

        self._token_usage_counter = Counter(
            "agent_token_usage_total",
            "Total token consumption by agent",
            ["agent", "model", "token_type"],
            registry=self._registry,
        )

        self._agent_calls_counter = Counter(
            "agent_calls_total",
            "Total number of agent calls",
            ["agent", "status"],
            registry=self._registry,
        )

        self._agent_latency = Histogram(
            "agent_latency_seconds",
            "Agent execution time in seconds",
            ["agent", "model"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            registry=self._registry,
        )

        self._tool_calls_counter = Counter(
            "tool_calls_total",
            "Total tool invocations",
            ["tool", "agent", "status"],
            registry=self._registry,
        )

        self._errors_counter = Counter(
            "agent_errors_total",
            "Total errors encountered",
            ["agent", "error_type"],
            registry=self._registry,
        )

        self._active_agents_gauge = Gauge(
            "active_agents",
            "Number of currently active agents",
            registry=self._registry,
        )

        self._memory_usage_gauge = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
            ["agent"],
            registry=self._registry,
        )

        self._queue_size_gauge = Gauge(
            "agent_queue_size",
            "Number of pending tasks in agent queue",
            ["agent"],
            registry=self._registry,
        )

        self._agent_info = Info(
            "agent_info",
            "Agent metadata information",
            ["agent"],
            registry=self._registry,
        )

        self._active_agents: Dict[str, int] = {}
        self._token_history: List[TokenUsage] = []

    def record_token_usage(
        self, agent_name: str, input_tokens: int, output_tokens: int, model_name: str
    ) -> None:
        """Record token usage for an agent call.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        input_tokens : int
            Number of input tokens.
        output_tokens : int
            Number of output tokens.
        model_name : str
            Model used for the call.
        """
        self._token_usage_counter.labels(
            agent=agent_name, model=model_name, token_type="input"
        ).inc(input_tokens)

        self._token_usage_counter.labels(
            agent=agent_name, model=model_name, token_type="output"
        ).inc(output_tokens)

        self._token_history.append(
            TokenUsage(
                agent_name=agent_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                model_name=model_name,
            )
        )

    def record_agent_call(
        self, agent_name: str, status: str = "success", model_name: str = "unknown"
    ) -> None:
        """Record an agent call.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        status : str
            Call status (success, error, timeout).
        model_name : str
            Model used for the call.
        """
        self._agent_calls_counter.labels(agent=agent_name, status=status).inc()
        self._agent_info.labels(agent=agent_name).info(
            {
                "model": model_name,
                "last_call": datetime.utcnow().isoformat(),
                "status": status,
            }
        )

    def record_tool_call(
        self, tool_name: str, agent_name: str, status: str = "success"
    ) -> None:
        """Record a tool invocation.

        Parameters
        ----------
        tool_name : str
            Name of the tool.
        agent_name : str
            Agent that called the tool.
        status : str
            Call status.
        """
        self._tool_calls_counter.labels(
            tool=tool_name, agent=agent_name, status=status
        ).inc()

    def record_error(self, agent_name: str, error_type: str) -> None:
        """Record an error encountered by an agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        error_type : str
            Type of error (timeout, validation, execution, etc).
        """
        self._errors_counter.labels(agent=agent_name, error_type=error_type).inc()

    @contextmanager
    def track_agent_latency(self, agent_name: str, model_name: str = "unknown"):
        """Context manager to track agent execution time.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        model_name : str
            Model used for the call.

        Yields
        -------
        None
        """
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self._agent_latency.labels(agent=agent_name, model=model_name).observe(
                duration
            )
        except Exception:
            duration = time.time() - start_time
            self._agent_latency.labels(agent=agent_name, model=model_name).observe(
                duration
            )
            raise

    def set_active_agents(self, count: int) -> None:
        """Update active agent count.

        Parameters
        ----------
        count : int
            Number of active agents.
        """
        self._active_agents_gauge.set(count)

    def increment_active_agents(self, agent_name: str) -> None:
        """Increment active agent count for specific agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        """
        self._active_agents[agent_name] = self._active_agents.get(agent_name, 0) + 1
        self._active_agents_gauge.set(sum(self._active_agents.values()))

    def decrement_active_agents(self, agent_name: str) -> None:
        """Decrement active agent count for specific agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        """
        if agent_name in self._active_agents:
            self._active_agents[agent_name] = max(
                0, self._active_agents[agent_name] - 1
            )
            self._active_agents_gauge.set(sum(self._active_agents.values()))

    def set_memory_usage(self, agent_name: str, usage_bytes: int) -> None:
        """Update memory usage for an agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        usage_bytes : int
            Memory usage in bytes.
        """
        self._memory_usage_gauge.labels(agent=agent_name).set(usage_bytes)

    def set_queue_size(self, agent_name: str, size: int) -> None:
        """Update queue size for an agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        size : int
            Queue size.
        """
        self._queue_size_gauge.labels(agent=agent_name).set(size)

    def get_token_usage_summary(
        self, agent_name: Optional[str] = None
    ) -> Dict[str, int]:
        """Get summary of token usage.

        Parameters
        ----------
        agent_name : Optional[str]
            Filter by specific agent, or None for all.

        Returns
        -------
        Dict[str, int]
            Token usage summary.
        """
        history = self._token_history
        if agent_name:
            history = [t for t in history if t.agent_name == agent_name]

        return {
            "total_calls": len(history),
            "total_input_tokens": sum(t.input_tokens for t in history),
            "total_output_tokens": sum(t.output_tokens for t in history),
            "total_tokens": sum(t.total_tokens for t in history),
        }

    def get_token_usage_history(self, limit: int = 100) -> List[Dict[str, any]]:
        """Get recent token usage history.

        Parameters
        ----------
        limit : int
            Maximum number of records to return.

        Returns
        -------
        List[Dict[str, any]]
            Recent token usage records.
        """
        recent = self._token_history[-limit:]
        return [
            {
                "agent": t.agent_name,
                "input_tokens": t.input_tokens,
                "output_tokens": t.output_tokens,
                "total_tokens": t.total_tokens,
                "model": t.model_name,
                "timestamp": t.timestamp,
            }
            for t in recent
        ]

    def start_metrics_server(self, port: int = 8000) -> None:
        """Start Prometheus metrics HTTP server.

        Parameters
        ----------
        port : int
            Port to run metrics server on.
        """
        start_http_server(port, registry=self._registry)

    def create_asgi_app(self):
        """Create ASGI app for metrics endpoint.

        Returns
        -------
        ASGI app
            ASGI application for /metrics endpoint.
        """
        return make_asgi_app(registry=self._registry)

    def track_tokens(self, agent_name: str):
        """Decorator to track token usage for agent functions.

        Parameters
        ----------
        agent_name : str
            Name of the agent.

        Returns
        -------
        Callable
            Decorated function.
        """

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.track_agent_latency(agent_name):
                    result = await func(*args, **kwargs)

                self.record_agent_call(agent_name, status="success")
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.track_agent_latency(agent_name):
                    result = func(*args, **kwargs)

                self.record_agent_call(agent_name, status="success")
                return result

            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator


# Singleton instance
_metrics: Optional[AgentMetrics] = None


def get_metrics(registry: Optional[CollectorRegistry] = None) -> AgentMetrics:
    """Get or create singleton metrics instance.

    Parameters
    ----------
    registry : Optional[CollectorRegistry]
        Prometheus registry to use.

    Returns
    -------
    AgentMetrics
        The metrics instance.
    """
    global _metrics
    if _metrics is None:
        _metrics = AgentMetrics(registry)
    return _metrics


if __name__ == "__main__":
    metrics = AgentMetrics()

    print("Starting metrics server on port 8000...")
    metrics.start_metrics_server(8000)

    print("Recording sample metrics...")
    metrics.record_agent_call("planner", "success", "gpt-4")
    metrics.record_token_usage("coder", 100, 50, "gpt-4")
    metrics.record_tool_call("save_file", "coder", "success")

    with metrics.track_agent_latency("critic", "gpt-4"):
        time.sleep(0.5)

    print("Metrics available at http://localhost:8000/metrics")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
