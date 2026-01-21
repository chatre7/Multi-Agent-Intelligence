"""Unit tests for Metrics System."""

import pytest
import time
from metrics import AgentMetrics, get_metrics, TokenUsage


class TestTokenUsage:
    """Test suite for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test TokenUsage dataclass creation."""
        usage = TokenUsage(
            agent_name="coder",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model_name="gpt-4",
        )

        assert usage.agent_name == "coder"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
        assert usage.model_name == "gpt-4"
        assert usage.timestamp > 0


class TestAgentMetrics:
    """Test suite for AgentMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics for each test."""
        return AgentMetrics()

    def test_initialization(self, metrics):
        """Test metrics initializes correctly."""
        assert metrics._registry is not None
        assert metrics._active_agents == {}
        assert len(metrics._token_history) == 0

    def test_record_token_usage(self, metrics):
        """Test recording token usage."""
        metrics.record_token_usage("coder", 100, 50, "gpt-4")

        assert len(metrics._token_history) == 1
        assert metrics._token_history[0].agent_name == "coder"
        assert metrics._token_history[0].input_tokens == 100
        assert metrics._token_history[0].output_tokens == 50
        assert metrics._token_history[0].total_tokens == 150

    def test_record_agent_call(self, metrics):
        """Test recording agent call."""
        metrics.record_agent_call("planner", "success", "gpt-4")

        assert metrics._active_agents == {}

    def test_record_agent_call_error(self, metrics):
        """Test recording failed agent call."""
        metrics.record_agent_call("tester", "error", "gpt-4")

        assert len(metrics._token_history) == 0  # No token history yet

    def test_record_tool_call(self, metrics):
        """Test recording tool call."""
        metrics.record_tool_call("save_file", "coder", "success")

        assert len(metrics._token_history) == 0

    def test_record_tool_call_error(self, metrics):
        """Test recording failed tool call."""
        metrics.record_tool_call("run_script", "tester", "error")

        assert len(metrics._token_history) == 0

    def test_record_error(self, metrics):
        """Test recording agent error."""
        metrics.record_error("critic", "validation")

        assert len(metrics._token_history) == 0

    def test_track_agent_latency_context_manager(self, metrics):
        """Test latency tracking context manager."""
        with metrics.track_agent_latency("planner", "gpt-4"):
            time.sleep(0.01)

        assert len(metrics._token_history) == 0  # No token history

    def test_track_agent_latency_exception(self, metrics):
        """Test latency tracking handles exceptions."""
        with pytest.raises(ValueError):
            with metrics.track_agent_latency("coder", "gpt-4"):
                time.sleep(0.01)
                raise ValueError("Test error")

        assert len(metrics._token_history) == 0

    def test_increment_active_agents(self, metrics):
        """Test incrementing active agents."""
        metrics.increment_active_agents("planner")

        assert "planner" in metrics._active_agents
        assert metrics._active_agents["planner"] == 1

        metrics.increment_active_agents("planner")
        assert metrics._active_agents["planner"] == 2

    def test_decrement_active_agents(self, metrics):
        """Test decrementing active agents."""
        metrics._active_agents["planner"] = 3

        metrics.decrement_active_agents("planner")
        assert metrics._active_agents["planner"] == 2

    def test_decrement_active_agents_no_negative(self, metrics):
        """Test decrement doesn't go below zero."""
        metrics._active_agents["planner"] = 0

        metrics.decrement_active_agents("planner")
        assert metrics._active_agents["planner"] == 0

    def test_set_memory_usage(self, metrics):
        """Test setting memory usage."""
        metrics.set_memory_usage("coder", 1024000)

        assert metrics._memory_usage_gauge is not None

    def test_set_queue_size(self, metrics):
        """Test setting queue size."""
        metrics.set_queue_size("planner", 5)

        assert metrics._queue_size_gauge is not None

    def test_get_token_usage_summary(self, metrics):
        """Test getting token usage summary."""
        metrics.record_token_usage("coder", 100, 50, "gpt-4")
        metrics.record_token_usage("tester", 50, 25, "gpt-4")

        summary = metrics.get_token_usage_summary()

        assert summary["total_calls"] == 2
        assert summary["total_input_tokens"] == 150
        assert summary["total_output_tokens"] == 75
        assert summary["total_tokens"] == 225

    def test_get_token_usage_summary_by_agent(self, metrics):
        """Test getting summary for specific agent."""
        metrics.record_token_usage("coder", 100, 50, "gpt-4")
        metrics.record_token_usage("tester", 50, 25, "gpt-4")

        summary = metrics.get_token_usage_summary("coder")

        assert summary["total_calls"] == 1
        assert summary["total_input_tokens"] == 100
        assert summary["total_output_tokens"] == 50

    def test_get_token_usage_history(self, metrics):
        """Test getting token usage history."""
        for i in range(5):
            metrics.record_token_usage(f"agent{i}", 100, 50, "gpt-4")

        history = metrics.get_token_usage_history(limit=3)

        assert len(history) == 3
        assert "agent" in history[0]
        assert "total_tokens" in history[0]
        assert "timestamp" in history[0]

    def test_get_token_usage_history_default_limit(self, metrics):
        """Test history with default limit."""
        for i in range(5):
            metrics.record_token_usage(f"agent{i}", 100, 50, "gpt-4")

        history = metrics.get_token_usage_history()

        assert len(history) == 5
        assert len(history) <= 100

    def test_create_asgi_app(self, metrics):
        """Test creating ASGI app."""
        app = metrics.create_asgi_app()

        assert app is not None
        assert callable(app)

    def test_track_tokens_decorator(self, metrics):
        """Test track_tokens decorator."""

        @metrics.track_tokens("planner")
        def planner_function():
            time.sleep(0.01)
            return "result"

        result = planner_function()

        assert result == "result"


class TestGetMetrics:
    """Test suite for get_metrics singleton."""

    def test_get_metrics_creates_instance(self):
        """Test get_metrics creates new instance."""
        from metrics import _metrics

        _metrics = None
        metrics = get_metrics()

        assert metrics is not None
        assert isinstance(metrics, AgentMetrics)

    def test_get_metrics_returns_singleton(self):
        """Test get_metrics returns same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_get_metrics_with_custom_registry(self):
        """Test get_metrics with custom registry."""
        from prometheus_client import CollectorRegistry
        from metrics import _metrics

        # Reset singleton to allow custom registry
        import metrics as metrics_module
        metrics_module._metrics = None

        custom_registry = CollectorRegistry()
        metrics = get_metrics(custom_registry)

        assert metrics._registry is custom_registry
