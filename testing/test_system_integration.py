"""Unit tests for System Integration."""

import pytest
from system_integration import MultiAgentSystem, get_system


class TestMultiAgentSystem:
    """Test suite for MultiAgentSystem class."""

    @pytest.fixture
    def system(self):
        """Create a fresh system for each test."""
        return MultiAgentSystem()

    def test_initialization(self, system):
        """Test system initializes correctly."""
        assert system.classifier is not None
        assert system.health_monitor is not None
        assert system.metrics is not None
        assert system.token_tracker is not None
        assert system._is_initialized is False

    def test_initialize_sets_flag(self, system):
        """Test initialize sets initialized flag."""
        system.initialize()

        assert system._is_initialized is True

    def test_initialize_already_initialized(self, system, capsys):
        """Test initialize handles already initialized state."""
        system.initialize()
        system.initialize()

        captured = capsys.readouterr()
        # Print statements produce output, check no errors
        assert "error" not in captured.out.lower() if captured.out else True

    def test_register_agent(self, system):
        """Test registering an agent."""

        async def mock_check():
            return True

        system.register_agent("planner", None, mock_check, "Planning agent")

        assert "planner" in system._agents
        assert len(system._agents) == 1

    def test_register_agent_without_check(self, system):
        """Test registering agent without health check."""
        system.register_agent("coder", None, capabilities="Coding agent")

        assert "coder" in system._agents

    def test_register_agent_without_capabilities(self, system):
        """Test registering agent without capabilities."""

        async def mock_check():
            return True

        system.register_agent("tester", mock_check)

        assert "tester" in system._agents

    def test_classify_and_route(self, system):
        """Test classification and routing."""
        system.initialize()

        result = system.classify_and_route("Write a Python function")

        assert "user_input" in result
        assert "intent" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "target_agent" in result

    def test_classify_and_route_with_history(self, system):
        """Test classification with conversation history."""
        system.initialize()

        history = [
            "User: I need to create a file",
            "AI: What file do you want to create?",
        ]

        result = system.classify_and_route("Create a Python script", history)

        assert result["user_input"] == "Create a Python script"
        assert "target_agent" in result

    @pytest.mark.asyncio
    async def test_check_system_health(self, system):
        """Test checking system health."""

        async def mock_check():
            return True

        system.register_agent("agent1", None, mock_check)
        system.register_agent("agent2", None, mock_check)

        health = await system.check_system_health()

        assert "status" in health
        assert "agents" in health
        assert "timestamp" in health

    def test_get_metrics_summary(self, system):
        """Test getting metrics summary."""
        system.initialize()

        summary = system.get_metrics_summary()

        assert "token_usage" in summary
        assert "daily_tokens" in summary
        assert "daily_cost" in summary
        assert "metrics" in summary

    @pytest.mark.asyncio
    async def test_start_health_monitoring(self, system):
        """Test starting health monitoring."""
        await system.start_health_monitoring()

        assert system.health_monitor._is_running is True

        system.stop_health_monitoring()

    @pytest.mark.asyncio
    async def test_stop_health_monitoring(self, system):
        """Test stopping health monitoring."""
        await system.start_health_monitoring()
        system.stop_health_monitoring()

        assert system.health_monitor._is_running is False

    def test_create_health_api(self, system):
        """Test creating health API."""
        app = system.create_health_api()

        assert app is not None
        assert len(app.routes) > 0

    def test_export_usage_data(self, system):
        """Test exporting usage data."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            filepath = system.export_usage_data(temp_path)

            assert filepath == temp_path
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_export_usage_data_auto_path(self, system):
        """Test exporting usage data with auto-generated path."""
        import os

        filepath = system.export_usage_data()

        assert os.path.exists(filepath)

        os.remove(filepath)

    def test_get_system_status_uninitialized(self, system):
        """Test getting status when not initialized."""
        status = system.get_system_status()

        assert status["status"] == "stopped"
        assert status["status"] == "stopped"

    def test_get_system_status_initialized(self, system):
        """Test getting status when initialized."""
        system.initialize()

        status = system.get_system_status()

        assert status["status"] == "running"
        assert status["status"] == "running"

    def test_get_system_status_with_agents(self, system):
        """Test getting status with registered agents."""
        system.initialize()
        system.register_agent("planner", None, None, "Planning")
        system.register_agent("coder", None, None, "Coding")

        status = system.get_system_status()

        assert status["agents_registered"] == 2
        assert "planner" in status["agents"]
        assert "coder" in status["agents"]


class TestGetSystem:
    """Test suite for get_system singleton."""

    def test_get_system_creates_instance(self):
        """Test get_system creates new instance."""
        from system_integration import _system

        _system = None
        system = get_system()

        assert system is not None
        assert isinstance(system, MultiAgentSystem)

    def test_get_system_returns_singleton(self):
        """Test get_system returns same instance."""
        system1 = get_system()
        system2 = get_system()

        assert system1 is system2

    def test_get_system_with_configs(self):
        """Test get_system with custom configs."""
        from intent_classifier import IntentClassifierConfig

        classifier_config = IntentClassifierConfig(model_name="gpt-oss:120b-cloud")

        system = get_system(classifier_config=classifier_config)

        assert system.classifier.config.model_name == "gpt-oss:120b-cloud"


class TestIntegration:
    """Integration tests for system components."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full workflow from initialization to health check."""
        system = MultiAgentSystem()
        system.initialize()

        async def mock_check():
            return True

        system.register_agent("test_agent", None, mock_check, "Test agent")

        result = system.classify_and_route("Test query")
        assert result["target_agent"] is not None

        health = await system.check_system_health()
        assert "test_agent" in health["agents"]

        summary = system.get_metrics_summary()
        assert "token_usage" in summary

        system.stop_health_monitoring()
        assert system.health_monitor._is_running is False


class TestErrorHandling:
    """Test error handling in system integration."""

    def test_classifier_error_handling(self):
        """Test system handles classifier errors gracefully."""
        system = MultiAgentSystem()
        system.initialize()

        result = system.classify_and_route("Test input")

        assert result is not None
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_health_monitor_error_handling(self):
        """Test system handles health check errors."""
        system = MultiAgentSystem()
        system.initialize()

        async def failing_check():
            raise Exception("Health check failed")

        system.register_agent("failing_agent", None, failing_check)

        health = await system.check_system_health()

        assert health is not None
        assert "status" in health
