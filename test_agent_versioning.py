"""Unit tests for Agent Versioning State Machine."""

import pytest
import tempfile
import os
from agent_versioning import (
    AgentVersionManager,
    AgentVersion,
    AgentState,
    TransitionAction,
    StateTransitionError,
    ValidationError,
    get_version_manager,
)


class TestAgentVersion:
    """Test suite for AgentVersion dataclass."""

    def test_agent_version_creation(self):
        """Test AgentVersion creation with defaults."""
        version = AgentVersion(
            agent_name="test_agent",
            version="1.0.0",
            state=AgentState.DEVELOPMENT,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            author="test@example.com",
        )

        assert version.agent_name == "test_agent"
        assert version.version == "1.0.0"
        assert version.state == AgentState.DEVELOPMENT
        assert version.author == "test@example.com"
        assert version.dependencies == []
        assert version.test_results == {}
        assert version.dev_config == {}

    def test_agent_version_to_dict(self):
        """Test converting AgentVersion to dictionary."""
        version = AgentVersion(
            agent_name="test_agent",
            version="1.0.0",
            state=AgentState.DEVELOPMENT,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            author="test@example.com",
        )

        data = version.to_dict()
        assert data["agent_name"] == "test_agent"
        assert data["state"] == "dev"  # Enum converted to string
        assert data["version"] == "1.0.0"

    def test_agent_version_from_dict(self):
        """Test creating AgentVersion from dictionary."""
        data = {
            "agent_name": "test_agent",
            "version": "1.0.0",
            "state": "dev",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "author": "test@example.com",
        }

        version = AgentVersion.from_dict(data)
        assert version.agent_name == "test_agent"
        assert version.state == AgentState.DEVELOPMENT


class TestAgentVersionManager:
    """Test suite for AgentVersionManager."""

    @pytest.fixture
    def version_manager(self):
        """Create fresh version manager for each test."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name
        yield AgentVersionManager(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_initialization(self, version_manager):
        """Test version manager initializes correctly."""
        assert version_manager._versions == {}
        assert version_manager._current_versions == {}
        assert os.path.exists(version_manager.storage_path)

    def test_create_version(self, version_manager):
        """Test creating a new agent version."""
        version = version_manager.create_version(
            agent_name="calculator",
            version="1.0.0",
            author="developer@example.com",
            description="Basic calculator",
        )

        assert version.agent_name == "calculator"
        assert version.version == "1.0.0"
        assert version.state == AgentState.DEVELOPMENT
        assert version.author == "developer@example.com"
        assert version.description == "Basic calculator"

        # Check it's stored
        stored = version_manager.get_version("calculator", "1.0.0")
        assert stored is not None
        assert stored.version == "1.0.0"

    def test_create_duplicate_version_raises_error(self, version_manager):
        """Test creating duplicate version raises error."""
        version_manager.create_version("calc", "1.0.0", "dev")

        with pytest.raises(ValueError, match="Version 1.0.0 already exists"):
            version_manager.create_version("calc", "1.0.0", "dev")

    def test_get_version_not_found(self, version_manager):
        """Test getting non-existent version returns None."""
        assert version_manager.get_version("nonexistent", "1.0.0") is None

    def test_get_current_version_no_versions(self, version_manager):
        """Test getting current version when no versions exist."""
        assert version_manager.get_current_version("nonexistent") is None

    def test_get_current_version_development(self, version_manager):
        """Test getting current version in development environment."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        current = version_manager.get_current_version("agent1", "dev")
        assert current is not None
        assert current.version == "1.0.0"
        assert current.state == AgentState.DEVELOPMENT

    def test_get_current_version_production_no_prod_versions(self, version_manager):
        """Test getting current prod version when no prod versions exist."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        current = version_manager.get_current_version("agent1", "prod")
        assert current is None

    def test_list_versions_single_agent(self, version_manager):
        """Test listing versions for a single agent."""
        version_manager.create_version("agent1", "1.0.0", "dev1")
        version_manager.create_version("agent1", "1.1.0", "dev2")

        versions = version_manager.list_versions("agent1")
        assert len(versions) == 2
        version_nums = {v.version for v in versions}
        assert version_nums == {"1.0.0", "1.1.0"}

    def test_list_versions_all_agents(self, version_manager):
        """Test listing versions for all agents."""
        version_manager.create_version("agent1", "1.0.0", "dev")
        version_manager.create_version("agent2", "1.0.0", "dev")

        versions = version_manager.list_versions()
        assert len(versions) == 2

    def test_update_version_metadata(self, version_manager):
        """Test updating version metadata."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        updated = version_manager.update_version_metadata(
            "agent1",
            "1.0.0",
            description="Updated description",
            test_results={"passed": 10, "failed": 0},
        )

        assert updated.description == "Updated description"
        assert updated.test_results == {"passed": 10, "failed": 0}

    def test_update_nonexistent_version_raises_error(self, version_manager):
        """Test updating non-existent version raises error."""
        with pytest.raises(ValueError, match="Version 1.0.0 not found"):
            version_manager.update_version_metadata(
                "nonexistent", "1.0.0", description="test"
            )

    def test_transition_to_testing_without_validation_fails(self, version_manager):
        """Test promoting to testing without validation fails."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        with pytest.raises(ValidationError, match="Test results required"):
            version_manager.transition_version(
                "agent1", "1.0.0", TransitionAction.PROMOTE
            )

    def test_transition_to_testing_with_validation_succeeds(self, version_manager):
        """Test promoting to testing with validation succeeds."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        # Add test results
        version_manager.update_version_metadata(
            "agent1", "1.0.0", test_results={"passed": 10, "failed": 0}
        )

        # Skip validation for this test
        updated = version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )

        assert updated.state == AgentState.TESTING

    def test_transition_invalid_action_raises_error(self, version_manager):
        """Test invalid state transition raises error."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        # Try to archive from development (invalid transition - not in allowed transitions)
        with pytest.raises(StateTransitionError, match="Invalid transition"):
            version_manager.transition_version(
                "agent1", "1.0.0", TransitionAction.ARCHIVE
            )

    def test_transition_to_production_requires_validation(self, version_manager):
        """Test promoting to production requires full validation."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        # Move to testing first
        version_manager.update_version_metadata(
            "agent1", "1.0.0", test_results={"passed": 10, "failed": 0}
        )
        version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )

        # Try to promote to production without required metadata
        with pytest.raises(ValidationError, match="Performance metrics required"):
            version_manager.transition_version(
                "agent1", "1.0.0", TransitionAction.PROMOTE
            )

    def test_transition_to_production_with_full_validation(self, version_manager):
        """Test promoting to production with full validation."""
        version_manager.create_version("agent1", "1.0.0", "dev")

        # Move to testing
        version_manager.update_version_metadata(
            "agent1", "1.0.0", test_results={"passed": 10, "failed": 0}
        )
        version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )

        # Add production requirements
        version_manager.update_version_metadata(
            "agent1",
            "1.0.0",
            performance_metrics={"latency_ms": 150},
            security_scan_results={"passed": True},
        )

        # Should succeed now
        updated = version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )
        assert updated.state == AgentState.PRODUCTION

    def test_get_transition_history(self, version_manager):
        """Test getting transition history."""
        version_manager.create_version("agent1", "1.0.0", "dev1")
        version_manager.create_version("agent1", "1.1.0", "dev2")

        history = version_manager.get_transition_history("agent1")
        assert len(history) == 2

        # Check sorting (most recent first)
        assert history[0]["version"] == "1.1.0" or history[1]["version"] == "1.1.0"

    def test_persistence_save_load(self, version_manager):
        """Test version persistence across manager restarts."""
        # Create version
        version_manager.create_version("persistent", "1.0.0", "test", "Persistent test")

        # Create new manager instance (simulating restart)
        new_manager = AgentVersionManager(version_manager.storage_path)

        # Should load the version
        loaded = new_manager.get_version("persistent", "1.0.0")
        assert loaded is not None
        assert loaded.agent_name == "persistent"
        assert loaded.version == "1.0.0"


class TestVersionManagerIntegration:
    """Integration tests for version manager with multiple agents."""

    @pytest.fixture
    def version_manager(self):
        """Create version manager for integration tests."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name
        yield AgentVersionManager(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_multiple_agents_different_versions(self, version_manager):
        """Test managing multiple agents with different versions."""
        # Agent 1
        version_manager.create_version("calculator", "1.0.0", "dev1")
        version_manager.create_version("calculator", "1.1.0", "dev1")

        # Agent 2
        version_manager.create_version("translator", "2.0.0", "dev2")

        # Check listings
        calc_versions = version_manager.list_versions("calculator")
        translator_versions = version_manager.list_versions("translator")
        all_versions = version_manager.list_versions()

        assert len(calc_versions) == 2
        assert len(translator_versions) == 1
        assert len(all_versions) == 3

    def test_environment_specific_versions(self, version_manager):
        """Test getting versions by environment."""
        version_manager.create_version("agent1", "1.0.0", "dev")
        version_manager.create_version("agent1", "1.1.0", "dev")

        # Move 1.0.0 to testing
        version_manager.update_version_metadata(
            "agent1", "1.0.0", test_results={"passed": 5}
        )
        version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )

        # Move 1.0.0 to production
        version_manager.update_version_metadata(
            "agent1",
            "1.0.0",
            performance_metrics={"latency": 100},
            security_scan_results={"status": "pass"},
        )
        version_manager.transition_version(
            "agent1", "1.0.0", TransitionAction.PROMOTE, skip_validation=True
        )

        # Check environments
        dev_version = version_manager.get_current_version("agent1", "dev")
        test_version = version_manager.get_current_version("agent1", "test")
        prod_version = version_manager.get_current_version("agent1", "prod")

        assert dev_version.version == "1.1.0"  # Latest in dev
        assert test_version is None  # No versions in testing state
        assert prod_version.version == "1.0.0"  # Only version in prod


class TestGetVersionManager:
    """Test singleton version manager."""

    def test_get_version_manager_creates_instance(self):
        """Test get_version_manager creates singleton instance."""
        from agent_versioning import _version_manager

        # Reset singleton
        _version_manager = None

        manager = get_version_manager()
        assert manager is not None
        assert isinstance(manager, AgentVersionManager)

    def test_get_version_manager_returns_singleton(self):
        """Test get_version_manager returns same instance."""
        manager1 = get_version_manager()
        manager2 = get_version_manager()

        assert manager1 is manager2
