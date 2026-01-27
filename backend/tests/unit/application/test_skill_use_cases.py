"""
Unit tests for skill use cases.
"""

import pytest

from src.domain.entities.agent import Agent, AgentState
from src.domain.entities.skill import Skill
from src.application.use_cases.skills import (
    get_effective_system_prompt,
    get_effective_tools,
)


class TestSkillUseCases:
    """Test skill-related use cases."""

    def test_get_effective_system_prompt_no_skills(self):
        """Test getting system prompt when agent has no skills."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are a helpful assistant.",
            capabilities=[],
            tools=[],
            model_name="gpt-4",
            skills=[],  # No skills
        )

        prompt = get_effective_system_prompt(agent, [])

        assert prompt == "You are a helpful assistant."

    def test_get_effective_system_prompt_with_one_skill(self):
        """Test getting system prompt with one skill."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are a helpful assistant.",
            capabilities=[],
            tools=[],
            model_name="gpt-4",
            skills=["python"],
        )

        skill = Skill(
            id="python",
            name="Python Expert",
            description="Python expertise",
            instructions="# Python Best Practices\n\nUse PEP 8 style.",
        )

        prompt = get_effective_system_prompt(agent, [skill])

        assert "You are a helpful assistant." in prompt
        assert "## Skill: Python Expert" in prompt
        assert "Python Best Practices" in prompt
        assert "Use PEP 8 style." in prompt

    def test_get_effective_system_prompt_with_multiple_skills(self):
        """Test getting system prompt with multiple skills."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Base prompt.",
            capabilities=[],
            tools=[],
            model_name="gpt-4",
            skills=["python", "testing"],
        )

        skills = [
            Skill(
                id="python",
                name="Python Expert",
                description="Python",
                instructions="Python instructions.",
            ),
            Skill(
                id="testing",
                name="Testing Expert",
                description="Testing",
                instructions="Testing instructions.",
            ),
        ]

        prompt = get_effective_system_prompt(agent, skills)

        assert "Base prompt." in prompt
        assert "## Skill: Python Expert" in prompt
        assert "Python instructions." in prompt
        assert "## Skill: Testing Expert" in prompt
        assert "Testing instructions." in prompt

    def test_get_effective_tools_no_skills(self):
        """Test getting tools when agent has no skills."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Test",
            capabilities=[],
            tools=["base_tool"],
            model_name="gpt-4",
            skills=[],
        )

        tools = get_effective_tools(agent, [])

        assert tools == ["base_tool"]

    def test_get_effective_tools_with_skills(self):
        """Test getting tools when skills provide additional tools."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Test",
            capabilities=[],
            tools=["base_tool"],
            model_name="gpt-4",
            skills=["python"],
        )

        skill = Skill(
            id="python",
            name="Python",
            description="Python",
            instructions="Python",
            tools=["execute_python", "read_file"],
        )

        tools = get_effective_tools(agent, [skill])

        assert "base_tool" in tools
        assert "execute_python" in tools
        assert "read_file" in tools
        assert len(tools) == 3

    def test_get_effective_tools_deduplication(self):
        """Test that duplicate tools are deduplicated."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Test",
            capabilities=[],
            tools=["read_file", "write_file"],
            model_name="gpt-4",
            skills=["file-ops"],
        )

        skill = Skill(
            id="file-ops",
            name="File Operations",
            description="File ops",
            instructions="File ops",
            tools=["read_file", "delete_file"],  # read_file is duplicate
        )

        tools = get_effective_tools(agent, [skill])

        # Should have unique tools only
        assert len(tools) == 3
        assert set(tools) == {"read_file", "write_file", "delete_file"}

    def test_get_effective_tools_multiple_skills(self):
        """Test getting tools from multiple skills."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Test",
            capabilities=[],
            tools=["base_tool"],
            model_name="gpt-4",
            skills=["skill1", "skill2"],
        )

        skills = [
            Skill(
                id="skill1",
                name="Skill 1",
                description="Skill 1",
                instructions="Skill 1",
                tools=["tool_a", "tool_b"],
            ),
            Skill(
                id="skill2",
                name="Skill 2",
                description="Skill 2",
                instructions="Skill 2",
                tools=["tool_c", "tool_d"],
            ),
        ]

        tools = get_effective_tools(agent, skills)

        assert "base_tool" in tools
        assert "tool_a" in tools
        assert "tool_b" in tools
        assert "tool_c" in tools
        assert "tool_d" in tools
        assert len(tools) == 5

    def test_get_effective_tools_skill_without_tools(self):
        """Test that skills without tools don't break the function."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="Test",
            capabilities=[],
            tools=["base_tool"],
            model_name="gpt-4",
            skills=["knowledge-only"],
        )

        skill = Skill(
            id="knowledge-only",
            name="Knowledge Only",
            description="Just knowledge",
            instructions="Instructions only, no tools.",
            tools=[],  # No tools
        )

        tools = get_effective_tools(agent, [skill])

        assert tools == ["base_tool"]  # Only agent's tools
