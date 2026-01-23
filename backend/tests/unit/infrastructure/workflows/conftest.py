"""
Pytest configuration for workflow strategy tests.

Uses isolated imports to avoid loading graph_builder and its heavy dependencies.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Mock heavy imports BEFORE importing our modules
# This prevents the import chain: workflow_strategies -> ... -> transformers
if 'transformers' not in sys.modules:
    sys.modules['transformers'] = MagicMock()
    sys.modules['transformers.GPT2TokenizerFast'] = MagicMock()

# Now safe to import without triggering heavy dependencies
from src.domain.entities import Agent, DomainConfig
from src.domain.value_objects import AgentState, SemanticVersion


@pytest.fixture
def orchestrator_domain() -> DomainConfig:
    """Domain configured for orchestrator workflow."""
    return DomainConfig(
        id="software_development",
        name="Software Development",
        description="Domain for software development with orchestrator workflow",
        agents=["planner", "coder", "tester", "reviewer"],
        default_agent="planner",
        workflow_type="supervisor",
        max_iterations=15,
        metadata={
            "workflow_type": "orchestrator",
            "orchestration": {
                "strategy": "deterministic",
                "pipeline": ["planner", "coder", "tester", "reviewer"],
                "continue_on_error": False,
            },
        },
    )


@pytest.fixture
def few_shot_domain() -> DomainConfig:
    """Domain configured for few-shot workflow."""
    return DomainConfig(
        id="social_chat",
        name="Social Chat",
        description="Domain for social interactions with few-shot workflow",
        agents=["empath", "comedian", "philosopher", "storyteller"],
        default_agent="empath",
        workflow_type="supervisor",
        max_iterations=5,
        metadata={
            "workflow_type": "few_shot",
            "few_shot": {
                "examples_enabled": True,
                "max_handoffs": 5,
                "handoff_confidence_threshold": 0.7,
            },
        },
    )


@pytest.fixture
def hybrid_domain() -> DomainConfig:
    """Domain configured for hybrid workflow."""
    return DomainConfig(
        id="research",
        name="Research",
        description="Domain for research tasks with hybrid workflow",
        agents=["planner", "searcher", "analyst", "validator"],
        default_agent="planner",
        workflow_type="supervisor",
        max_iterations=10,
        metadata={
            "workflow_type": "hybrid",
            "hybrid": {
                "orchestrator_decides": ["planning", "validation"],
                "llm_decides": ["agent_selection", "handoff_timing"],
            },
        },
    )


@pytest.fixture
def planner_agent() -> Agent:
    """Create a planner agent."""
    return Agent(
        id="planner",
        name="Planner",
        domain_id="software_development",
        description="Plans software development tasks",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are a software planning expert.",
        capabilities=["planning", "architecture"],
        tools=["search_memory"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.7,
        max_tokens=2048,
        keywords=["plan", "design", "architecture"],
    )


@pytest.fixture
def coder_agent() -> Agent:
    """Create a coder agent."""
    return Agent(
        id="coder",
        name="Coder",
        domain_id="software_development",
        description="Writes code based on specifications",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are an expert Python developer.",
        capabilities=["python", "code_review", "debugging"],
        tools=["save_file", "search_memory"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.0,
        max_tokens=4096,
        keywords=["code", "implement", "write", "create"],
    )


@pytest.fixture
def tester_agent() -> Agent:
    """Create a tester agent."""
    return Agent(
        id="tester",
        name="Tester",
        domain_id="software_development",
        description="Tests code and verifies correctness",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are a quality assurance expert.",
        capabilities=["testing", "quality_assurance"],
        tools=["run_tests", "search_memory"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.2,
        max_tokens=2048,
        keywords=["test", "verify", "validate"],
    )


@pytest.fixture
def reviewer_agent() -> Agent:
    """Create a reviewer agent."""
    return Agent(
        id="reviewer",
        name="Reviewer",
        domain_id="software_development",
        description="Reviews code for quality and best practices",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are a code review expert.",
        capabilities=["code_review", "security"],
        tools=["search_memory"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.3,
        max_tokens=2048,
        keywords=["review", "check", "audit"],
    )


@pytest.fixture
def software_dev_agents(
    planner_agent: Agent,
    coder_agent: Agent,
    tester_agent: Agent,
    reviewer_agent: Agent,
) -> dict[str, Agent]:
    """Dictionary of software development agents."""
    return {
        "planner": planner_agent,
        "coder": coder_agent,
        "tester": tester_agent,
        "reviewer": reviewer_agent,
    }


@pytest.fixture
def empath_agent() -> Agent:
    """Create an empath agent for social chat."""
    return Agent(
        id="empath",
        name="Empath",
        domain_id="social_chat",
        description="Understands and responds to emotions",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are an empathetic conversationalist.",
        capabilities=["emotional_intelligence", "counseling"],
        tools=["transfer_to_agent"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.8,
        max_tokens=1024,
        keywords=["feel", "emotion", "sad", "happy"],
    )


@pytest.fixture
def comedian_agent() -> Agent:
    """Create a comedian agent for social chat."""
    return Agent(
        id="comedian",
        name="Comedian",
        domain_id="social_chat",
        description="Tells jokes and makes people laugh",
        version=SemanticVersion(1, 0, 0),
        state=AgentState.PRODUCTION,
        system_prompt="You are a professional comedian.",
        capabilities=["humor", "entertainment"],
        tools=["transfer_to_agent"],
        model_name="gpt-oss:120b-cloud",
        temperature=0.9,
        max_tokens=1024,
        keywords=["joke", "funny", "laugh", "humor"],
    )


@pytest.fixture
def social_chat_agents(
    empath_agent: Agent,
    comedian_agent: Agent,
) -> dict[str, Agent]:
    """Dictionary of social chat agents."""
    return {
        "empath": empath_agent,
        "comedian": comedian_agent,
    }
