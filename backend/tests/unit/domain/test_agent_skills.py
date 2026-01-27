"""
Integration tests for Agent with Skills.
"""

import pytest

from src.domain.entities.agent import Agent, AgentState


class TestAgentWithSkills:
    """Test Agent entity with skills field."""

    def test_agent_creation_without_skills(self):
        """Test creating agent without skills (default empty)."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test agent",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are helpful.",
            capabilities=["general"],
            tools=["tool1"],
            model_name="gpt-4",
        )

        assert agent.skills == []  # Default empty

    def test_agent_creation_with_skills(self):
        """Test creating agent with skills."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test agent",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are helpful.",
            capabilities=["general"],
            tools=["tool1"],
            model_name="gpt-4",
            skills=["python-engineering", "code-review"],
        )

        assert len(agent.skills) == 2
        assert "python-engineering" in agent.skills
        assert "code-review" in agent.skills

    def test_agent_to_dict_includes_skills(self):
        """Test that to_dict includes skills field."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test agent",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are helpful.",
            capabilities=["general"],
            tools=["tool1"],
            model_name="gpt-4",
            skills=["skill1", "skill2"],
        )

        data = agent.to_dict()

        assert "skills" in data
        assert data["skills"] == ["skill1", "skill2"]

    def test_agent_to_dict_empty_skills(self):
        """Test that to_dict includes empty skills list."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test agent",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are helpful.",
            capabilities=["general"],
            tools=["tool1"],
            model_name="gpt-4",
            skills=[],
        )

        data = agent.to_dict()

        assert "skills" in data
        assert data["skills"] == []

    def test_agent_from_dict_with_skills(self):
        """Test deserializing agent with skills."""
        data = {
            "id": "test-agent",
            "name": "Test Agent",
            "domain_id": "test",
            "description": "Test agent",
            "version": "1.0.0",
            "state": "production",
            "system_prompt": "You are helpful.",
            "capabilities": ["general"],
            "tools": ["tool1"],
            "model_name": "gpt-4",
            "skills": ["python", "testing"],
        }

        agent = Agent.from_dict(data)

        assert agent.skills == ["python", "testing"]

    def test_agent_from_dict_without_skills(self):
        """Test deserializing agent without skills field (backward compat)."""
        data = {
            "id": "test-agent",
            "name": "Test Agent",
            "domain_id": "test",
            "description": "Test agent",
            "version": "1.0.0",
            "state": "production",
            "system_prompt": "You are helpful.",
            "capabilities": ["general"],
            "tools": ["tool1"],
            "model_name": "gpt-4",
            # No skills field
        }

        agent = Agent.from_dict(data)

        assert agent.skills == []  # Default empty

    def test_agent_skills_immutability(self):
        """Test that skills list can be modified after creation."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            domain_id="test",
            description="Test agent",
            version="1.0.0",
            state=AgentState.PRODUCTION,
            system_prompt="You are helpful.",
            capabilities=["general"],
            tools=["tool1"],
            model_name="gpt-4",
            skills=["skill1"],
        )

        # Should be able to modify skills
        agent.skills.append("skill2")
        assert len(agent.skills) == 2

