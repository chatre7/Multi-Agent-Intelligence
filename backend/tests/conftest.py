"""
Pytest configuration and shared fixtures.

Includes monkeypatching to avoid heavy imports during test collection.
"""

import pytest
import sys
from unittest.mock import MagicMock

from src.domain.entities import Agent, DomainConfig, Tool
from src.domain.value_objects import AgentState, SemanticVersion


# ========== MOCK HEAVY DEPENDENCIES ==========
# Prevent slow imports during test collection

@pytest.fixture(scope="session", autouse=True)
def mock_heavy_imports():
    """Mock heavy dependencies to speed up test collection."""
    # Mock transformers - this is what's causing the 11-minute delay
    sys.modules['transformers'] = MagicMock()
    sys.modules['transformers.GPT2TokenizerFast'] = MagicMock()
    
    # Mock other heavy ML libraries if needed
    sys.modules['torch'] = MagicMock()
    sys.modules['tensorflow'] = MagicMock()
    
    yield
    
    # Cleanup (optional, usually not needed in session scope)
    # for module in ['transformers', 'torch', 'tensorflow']:
    #     sys.modules.pop(module, None)


# ========== EXISTING FIXTURES ==========

@pytest.fixture
def sample_version() -> SemanticVersion:
    """Create a sample semantic version."""
    return SemanticVersion(1, 0, 0)


@pytest.fixture
def sample_agent_state() -> AgentState:
    """Create a sample agent state."""
    return AgentState.PRODUCTION


@pytest.fixture
def sample_agent(sample_version: SemanticVersion) -> Agent:
    """Create a sample agent for testing."""
    return Agent(
        id="coder-001",
        name="Coder",
        domain_id="software_development",
        description="Expert Python developer",
        version=sample_version,
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


@pytest.fixture
def sample_domain() -> DomainConfig:
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


@pytest.fixture
def sample_tool() -> Tool:
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


@pytest.fixture
def development_agent() -> Agent:
    """Create an agent in development state."""
    return Agent(
        id="dev-agent",
        name="Development Agent",
        domain_id="test",
        description="Agent in development",
        version=SemanticVersion(0, 1, 0),
        state=AgentState.DEVELOPMENT,
        system_prompt="Test prompt",
        capabilities=["test"],
        tools=[],
        model_name="test-model",
    )
