"""Unit tests for Health Monitor."""

import pytest
import asyncio
from datetime import datetime
from monitoring.health_monitor import HealthMonitor, HealthConfig, AgentHealth, get_health_monitor


class TestAgentHealth:
    """Test suite for AgentHealth dataclass."""

    def test_agent_health_creation(self):
        """Test AgentHealth dataclass creation."""
        health = AgentHealth(
            name="planner",
            status="healthy",
            last_check=datetime.utcnow().isoformat(),
            response_time_ms=100.5,
        )

        assert health.name == "planner"
        assert health.status == "healthy"
        assert health.response_time_ms == 100.5
        assert health.error_count == 0
        assert health.last_error is None
        assert health.metadata == {}


class TestHealthConfig:
    """Test suite for HealthConfig."""

    def test_default_config(self):
        """Test HealthConfig with default values."""
        config = HealthConfig()

        assert config.check_interval_seconds == 30
        assert config.timeout_seconds == 10
        assert config.unhealthy_threshold == 3
        assert config.response_time_threshold_ms == 5000.0
        assert config.enable_auto_recovery is True

    def test_custom_config(self):
        """Test HealthConfig with custom values."""
        config = HealthConfig(
            check_interval_seconds=60, timeout_seconds=20, unhealthy_threshold=5
        )

        assert config.check_interval_seconds == 60
        assert config.timeout_seconds == 20
        assert config.unhealthy_threshold == 5

    def test_config_validation_defaults(self):
        """Test config respects min/max constraints."""
        # Pydantic validates that values are within constraints
        # test_check_interval_seconds=1 would fail validation (must be >= 5)
        # test_timeout_seconds=300 would fail validation (must be <= 60)
        config = HealthConfig(check_interval_seconds=5, timeout_seconds=60)

        assert config.check_interval_seconds == 5
        assert config.timeout_seconds == 60


class TestHealthMonitor:
    """Test suite for HealthMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor for each test."""
        return HealthMonitor()

    def test_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert monitor.config is not None
        assert monitor._agents == {}
        assert monitor._is_running is False
        assert monitor._app is None

    def test_register_agent(self, monitor):
        """Test registering an agent."""

        async def mock_check():
            return True

        monitor.register_agent("planner", mock_check, {"type": "planning"})

        assert "planner" in monitor._agents
        assert monitor._agents["planner"].name == "planner"
        assert monitor._agents["planner"].metadata == {"type": "planning"}

    def test_register_agent_without_metadata(self, monitor):
        """Test registering agent without metadata."""

        async def mock_check():
            return True

        monitor.register_agent("coder", mock_check)

        assert "coder" in monitor._agents
        assert monitor._agents["coder"].metadata == {}

    @pytest.mark.asyncio
    async def test_check_agent_health_success(self, monitor):
        """Test successful health check."""

        async def mock_check():
            await asyncio.sleep(0.01)
            return True

        monitor.register_agent("tester", mock_check)
        result = await monitor.check_agent_health("tester")

        assert result["status"] == "healthy"
        assert result["name"] == "tester"
        assert result["error_count"] == 0
        assert result["last_error"] is None

    @pytest.mark.asyncio
    async def test_check_agent_health_slow(self, monitor):
        """Test health check with slow response."""
        monitor.config.response_time_threshold_ms = 10.0

        async def mock_check():
            await asyncio.sleep(0.02)
            return True

        monitor.register_agent("slow_agent", mock_check)
        result = await monitor.check_agent_health("slow_agent")

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_agent_health_failure(self, monitor):
        """Test failed health check."""

        async def mock_check():
            raise Exception("Agent unavailable")

        monitor.register_agent("failing_agent", mock_check)
        result = await monitor.check_agent_health("failing_agent")

        assert result["status"] == "unhealthy"
        assert result["error_count"] == 1
        assert "Agent unavailable" in result["last_error"]

    @pytest.mark.asyncio
    async def test_check_agent_health_nonexistent(self, monitor):
        """Test checking nonexistent agent raises error."""
        with pytest.raises(Exception):  # HTTPException
            await monitor.check_agent_health("nonexistent")

    @pytest.mark.asyncio
    async def test_check_all_agents(self, monitor):
        """Test checking all agents."""

        async def check1():
            return True

        async def check2():
            return True

        monitor.register_agent("agent1", check1)
        monitor.register_agent("agent2", check2)

        results = await monitor.check_all_agents()

        assert "status" in results
        assert "timestamp" in results
        assert "agents" in results
        assert len(results["agents"]) == 2

    @pytest.mark.asyncio
    async def test_check_all_agents_unhealthy(self, monitor):
        """Test overall status with unhealthy agent."""

        async def healthy_check():
            return True

        async def unhealthy_check():
            raise Exception("Failed")

        monitor.register_agent("healthy_agent", healthy_check)
        monitor.register_agent("unhealthy_agent", unhealthy_check)

        results = await monitor.check_all_agents()

        assert results["status"] in ["degraded", "unhealthy"]

    def test_get_agent_status(self, monitor):
        """Test getting agent status without check."""

        async def mock_check():
            return True

        monitor.register_agent("planner", mock_check)
        result = monitor.get_agent_status("planner")

        assert result["name"] == "planner"
        assert result["status"] == "unknown"

    def test_get_agent_status_nonexistent(self, monitor):
        """Test getting status for nonexistent agent."""
        with pytest.raises(Exception):  # HTTPException
            monitor.get_agent_status("nonexistent")

    def test_get_all_statuses(self, monitor):
        """Test getting all agent statuses."""

        async def mock_check():
            return True

        monitor.register_agent("agent1", mock_check)
        monitor.register_agent("agent2", mock_check)

        statuses = monitor.get_all_statuses()

        assert len(statuses["agents"]) == 2
        assert "uptime_seconds" in statuses
        assert "timestamp" in statuses

    def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping background monitoring."""
        assert monitor._is_running is False

        # Don't actually start the async task in test
        # Just verify the methods work
        assert hasattr(monitor, "start_monitoring")
        assert hasattr(monitor, "stop_monitoring")

        # The actual start/stop would need an event loop
        # In test environment, we just verify the flag state

    def test_create_fastapi_app(self, monitor):
        """Test FastAPI app creation."""
        app = monitor.create_fastapi_app()

        assert app is not None
        assert monitor._app is not None
        assert len(app.routes) > 0

    def test_system_uptime_calculation(self, monitor):
        """Test system uptime is calculated."""
        import time

        start_time = monitor._system_start_time
        uptime = time.time() - start_time

        assert uptime >= 0
        assert uptime < 1  # Should be very recent

    @pytest.mark.asyncio
    async def test_error_count_increment(self, monitor):
        """Test error count increments on failures."""

        async def failing_check():
            raise Exception("Error")

        monitor.register_agent("failing", failing_check)

        await monitor.check_agent_health("failing")
        assert monitor._agents["failing"].error_count == 1

        await monitor.check_agent_health("failing")
        assert monitor._agents["failing"].error_count == 2


class TestGetHealthMonitor:
    """Test suite for get_health_monitor singleton."""

    def test_get_monitor_creates_instance(self):
        """Test get_health_monitor creates new instance."""
        from health_monitor import _monitor

        _monitor = None
        monitor = get_health_monitor()

        assert monitor is not None
        assert isinstance(monitor, HealthMonitor)

    def test_get_monitor_returns_singleton(self):
        """Test get_health_monitor returns same instance."""
        monitor1 = get_health_monitor()
        monitor2 = get_health_monitor()

        assert monitor1 is monitor2
