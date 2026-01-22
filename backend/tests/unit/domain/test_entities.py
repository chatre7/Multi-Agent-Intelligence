"""
Unit tests for Domain Entities.

TDD approach: Write tests first, then implement entities.
"""

import pytest

# These imports will fail initially - that's expected in TDD
from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
from src.domain.entities.tool import Tool
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


class TestAgentState:
    """Tests for AgentState value object."""

    def test_agent_state_values(self):
        """Test that all expected states exist."""
        assert AgentState.DEVELOPMENT.value == "development"
        assert AgentState.TESTING.value == "testing"
        assert AgentState.PRODUCTION.value == "production"
        assert AgentState.DEPRECATED.value == "deprecated"
        assert AgentState.ARCHIVED.value == "archived"

    def test_agent_state_from_string(self):
        """Test creating AgentState from string."""
        assert AgentState.from_string("development") == AgentState.DEVELOPMENT
        assert AgentState.from_string("production") == AgentState.PRODUCTION

    def test_agent_state_invalid_string(self):
        """Test invalid state string raises error."""
        with pytest.raises(ValueError):
            AgentState.from_string("invalid_state")

    def test_valid_transitions_from_development(self):
        """Test valid state transitions from DEVELOPMENT."""
        dev = AgentState.DEVELOPMENT
        assert dev.can_transition_to(AgentState.TESTING) is True
        assert dev.can_transition_to(AgentState.PRODUCTION) is False
        assert dev.can_transition_to(AgentState.DEPRECATED) is True

    def test_valid_transitions_from_testing(self):
        """Test valid state transitions from TESTING."""
        testing = AgentState.TESTING
        assert testing.can_transition_to(AgentState.PRODUCTION) is True
        assert testing.can_transition_to(AgentState.DEVELOPMENT) is True  # Demote
        assert testing.can_transition_to(AgentState.DEPRECATED) is True

    def test_valid_transitions_from_production(self):
        """Test valid state transitions from PRODUCTION."""
        prod = AgentState.PRODUCTION
        assert prod.can_transition_to(AgentState.DEPRECATED) is True
        assert prod.can_transition_to(AgentState.DEVELOPMENT) is False
        assert prod.can_transition_to(AgentState.TESTING) is False


class TestSemanticVersion:
    """Tests for SemanticVersion value object."""

    def test_create_version(self):
        """Test creating a semantic version."""
        version = SemanticVersion(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_to_string(self):
        """Test version string representation."""
        version = SemanticVersion(1, 2, 3)
        assert str(version) == "1.2.3"

    def test_version_from_string(self):
        """Test parsing version from string."""
        version = SemanticVersion.from_string("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_from_string_invalid(self):
        """Test invalid version string raises error."""
        with pytest.raises(ValueError):
            SemanticVersion.from_string("invalid")

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(1, 1, 0)
        v3 = SemanticVersion(2, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert v1 < v3

    def test_version_equality(self):
        """Test version equality."""
        v1 = SemanticVersion(1, 2, 3)
        v2 = SemanticVersion(1, 2, 3)
        assert v1 == v2

    def test_version_increment_patch(self):
        """Test incrementing patch version."""
        version = SemanticVersion(1, 2, 3)
        new_version = version.increment_patch()
        assert str(new_version) == "1.2.4"

    def test_version_increment_minor(self):
        """Test incrementing minor version resets patch."""
        version = SemanticVersion(1, 2, 3)
        new_version = version.increment_minor()
        assert str(new_version) == "1.3.0"

    def test_version_increment_major(self):
        """Test incrementing major version resets minor and patch."""
        version = SemanticVersion(1, 2, 3)
        new_version = version.increment_major()
        assert str(new_version) == "2.0.0"


class TestAgent:
    """Tests for Agent entity."""

    @pytest.fixture
    def sample_agent(self) -> Agent:
        """Create a sample agent for testing."""
        return Agent(
            id="coder-001",
            name="Coder",
            domain_id="software_development",
            description="Expert Python developer",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are an expert Python developer.",
            capabilities=["python", "code_review", "debugging"],
            tools=["save_file", "search_memory"],
            model_name="gpt-oss:120b-cloud",
            temperature=0.0,
            max_tokens=4096,
            keywords=["code", "implement", "write", "create"],
            author="system",
        )

    def test_agent_creation(self, sample_agent: Agent):
        """Test agent is created with correct attributes."""
        assert sample_agent.id == "coder-001"
        assert sample_agent.name == "Coder"
        assert sample_agent.domain_id == "software_development"
        assert sample_agent.state == AgentState.PRODUCTION
        assert len(sample_agent.capabilities) == 3
        assert len(sample_agent.tools) == 2

    def test_agent_can_handle_matching_keywords(self, sample_agent: Agent):
        """Test agent confidence for matching keywords."""
        confidence = sample_agent.can_handle(intent="code", keywords=["code", "python"])
        assert confidence > 0.0

    def test_agent_can_handle_no_matching_keywords(self, sample_agent: Agent):
        """Test agent confidence for non-matching keywords."""
        confidence = sample_agent.can_handle(
            intent="deploy", keywords=["deploy", "kubernetes"]
        )
        assert confidence == 0.0

    def test_agent_promote_valid_transition(self, sample_agent: Agent):
        """Test valid state promotion."""
        # Create development agent
        dev_agent = Agent(
            id="test-001",
            name="Test",
            domain_id="test",
            description="Test agent",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.DEVELOPMENT,
            system_prompt="Test",
            capabilities=[],
            tools=[],
            model_name="test",
        )
        dev_agent.promote(AgentState.TESTING)
        assert dev_agent.state == AgentState.TESTING

    def test_agent_promote_invalid_transition(self, sample_agent: Agent):
        """Test invalid state promotion raises error."""
        # Production cannot go directly to development
        with pytest.raises(ValueError):
            sample_agent.promote(AgentState.DEVELOPMENT)

    def test_agent_has_capability(self, sample_agent: Agent):
        """Test checking agent capabilities."""
        assert sample_agent.has_capability("python") is True
        assert sample_agent.has_capability("javascript") is False

    def test_agent_has_tool(self, sample_agent: Agent):
        """Test checking agent tools."""
        assert sample_agent.has_tool("save_file") is True
        assert sample_agent.has_tool("delete_file") is False

    def test_agent_to_dict(self, sample_agent: Agent):
        """Test agent serialization to dictionary."""
        data = sample_agent.to_dict()
        assert data["id"] == "coder-001"
        assert data["name"] == "Coder"
        assert data["state"] == "production"
        assert data["version"] == "1.0.0"

    def test_agent_from_dict(self):
        """Test agent deserialization from dictionary."""
        data = {
            "id": "coder-001",
            "name": "Coder",
            "domain_id": "software_development",
            "description": "Expert Python developer",
            "version": "1.0.0",
            "state": "production",
            "system_prompt": "You are an expert Python developer.",
            "capabilities": ["python"],
            "tools": ["save_file"],
            "model_name": "gpt-oss:120b-cloud",
            "temperature": 0.0,
            "max_tokens": 4096,
            "keywords": ["code"],
            "author": "system",
        }
        agent = Agent.from_dict(data)
        assert agent.id == "coder-001"
        assert agent.state == AgentState.PRODUCTION


class TestDomainConfig:
    """Tests for DomainConfig entity."""

    @pytest.fixture
    def sample_domain(self) -> DomainConfig:
        """Create a sample domain for testing."""
        return DomainConfig(
            id="software_development",
            name="Software Development",
            description="Domain for software development tasks",
            agents=["planner", "coder", "tester", "reviewer"],
            default_agent="planner",
            workflow_type="supervisor",
            max_iterations=15,
            routing_rules=[
                {"keywords": ["code", "implement"], "agent": "coder", "priority": 1},
                {"keywords": ["test", "verify"], "agent": "tester", "priority": 2},
            ],
            fallback_agent="planner",
            allowed_roles=["user", "developer", "admin"],
        )

    def test_domain_creation(self, sample_domain: DomainConfig):
        """Test domain is created with correct attributes."""
        assert sample_domain.id == "software_development"
        assert sample_domain.name == "Software Development"
        assert len(sample_domain.agents) == 4
        assert sample_domain.default_agent == "planner"

    def test_domain_has_agent(self, sample_domain: DomainConfig):
        """Test checking if domain has agent."""
        assert sample_domain.has_agent("coder") is True
        assert sample_domain.has_agent("unknown") is False

    def test_domain_get_agent_for_keywords(self, sample_domain: DomainConfig):
        """Test routing keywords to correct agent."""
        agent = sample_domain.get_agent_for_keywords(["code", "python"])
        assert agent == "coder"

    def test_domain_get_agent_fallback(self, sample_domain: DomainConfig):
        """Test fallback agent for unknown keywords."""
        agent = sample_domain.get_agent_for_keywords(["unknown", "task"])
        assert agent == "planner"  # fallback

    def test_domain_is_role_allowed(self, sample_domain: DomainConfig):
        """Test role permission checking."""
        assert sample_domain.is_role_allowed("developer") is True
        assert sample_domain.is_role_allowed("guest") is False

    def test_domain_to_dict(self, sample_domain: DomainConfig):
        """Test domain serialization."""
        data = sample_domain.to_dict()
        assert data["id"] == "software_development"
        assert data["workflow_type"] == "supervisor"

    def test_domain_from_dict(self):
        """Test domain deserialization."""
        data = {
            "id": "test_domain",
            "name": "Test",
            "description": "Test domain",
            "agents": ["agent1"],
            "default_agent": "agent1",
            "workflow_type": "sequential",
            "max_iterations": 10,
            "routing_rules": [],
            "fallback_agent": "agent1",
            "allowed_roles": ["user"],
        }
        domain = DomainConfig.from_dict(data)
        assert domain.id == "test_domain"


class TestTool:
    """Tests for Tool entity."""

    @pytest.fixture
    def sample_tool(self) -> Tool:
        """Create a sample tool for testing."""
        return Tool(
            id="save_file",
            name="save_file",
            description="Saves content to a file",
            parameters_schema={
                "type": "object",
                "required": ["filename", "content"],
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
            returns_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "path": {"type": "string"},
                },
            },
            handler_path="src.infrastructure.tools.file_operations.save_file",
            timeout_seconds=30.0,
            max_retries=3,
            requires_approval=True,
            allowed_roles=["developer", "admin"],
            tags=["file", "io"],
            domain="software_development",
        )

    def test_tool_creation(self, sample_tool: Tool):
        """Test tool is created with correct attributes."""
        assert sample_tool.id == "save_file"
        assert sample_tool.requires_approval is True
        assert sample_tool.timeout_seconds == 30.0

    def test_tool_is_role_allowed(self, sample_tool: Tool):
        """Test role permission for tool."""
        assert sample_tool.is_role_allowed("developer") is True
        assert sample_tool.is_role_allowed("user") is False

    def test_tool_has_tag(self, sample_tool: Tool):
        """Test checking tool tags."""
        assert sample_tool.has_tag("file") is True
        assert sample_tool.has_tag("network") is False

    def test_tool_validate_parameters_valid(self, sample_tool: Tool):
        """Test parameter validation with valid params."""
        params = {"filename": "test.py", "content": "print('hello')"}
        is_valid, errors = sample_tool.validate_parameters(params)
        assert is_valid is True
        assert len(errors) == 0

    def test_tool_validate_parameters_missing_required(self, sample_tool: Tool):
        """Test parameter validation with missing required field."""
        params = {"filename": "test.py"}  # missing content
        is_valid, errors = sample_tool.validate_parameters(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_tool_to_dict(self, sample_tool: Tool):
        """Test tool serialization."""
        data = sample_tool.to_dict()
        assert data["id"] == "save_file"
        assert data["requires_approval"] is True

    def test_tool_from_dict(self):
        """Test tool deserialization."""
        data = {
            "id": "test_tool",
            "name": "test_tool",
            "description": "Test tool",
            "parameters_schema": {"type": "object"},
            "returns_schema": {"type": "object"},
            "handler_path": "test.handler",
            "timeout_seconds": 10.0,
            "max_retries": 1,
            "requires_approval": False,
            "allowed_roles": ["user"],
            "tags": [],
            "domain": None,
        }
        tool = Tool.from_dict(data)
        assert tool.id == "test_tool"


class TestAgentIntegration:
    """Integration tests for Agent entity behavior."""

    def test_agent_lifecycle_development_to_production(self):
        """Test full agent lifecycle from development to production."""
        agent = Agent(
            id="lifecycle-test",
            name="Lifecycle Test",
            domain_id="test",
            description="Test agent for lifecycle",
            version=SemanticVersion(0, 1, 0),
            state=AgentState.DEVELOPMENT,
            system_prompt="Test prompt",
            capabilities=["test"],
            tools=[],
            model_name="test-model",
        )

        # Development -> Testing
        assert agent.state == AgentState.DEVELOPMENT
        agent.promote(AgentState.TESTING)
        assert agent.state == AgentState.TESTING

        # Testing -> Production
        agent.promote(AgentState.PRODUCTION)
        assert agent.state == AgentState.PRODUCTION

        # Production -> Deprecated
        agent.promote(AgentState.DEPRECATED)
        assert agent.state == AgentState.DEPRECATED

        # Deprecated -> Archived
        agent.promote(AgentState.ARCHIVED)
        assert agent.state == AgentState.ARCHIVED

    def test_agent_cannot_skip_states(self):
        """Test that agents cannot skip states in lifecycle."""
        agent = Agent(
            id="skip-test",
            name="Skip Test",
            domain_id="test",
            description="Test agent",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.DEVELOPMENT,
            system_prompt="Test",
            capabilities=[],
            tools=[],
            model_name="test",
        )

        # Cannot skip directly from development to production
        with pytest.raises(ValueError):
            agent.promote(AgentState.PRODUCTION)
