"""
Unit tests for Skill entity.
"""

import pytest

from src.domain.entities.skill import Skill


class TestSkillEntity:
    """Test Skill entity behavior."""

    def test_skill_creation(self):
        """Test creating a skill with required fields."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            description="A test skill",
            instructions="# Test Instructions\nDo something.",
        )

        assert skill.id == "test-skill"
        assert skill.name == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.instructions == "# Test Instructions\nDo something."
        assert skill.tools == []  # Default empty

    def test_skill_with_tools(self):
        """Test creating a skill with tools."""
        skill = Skill(
            id="code-skill",
            name="Code Skill",
            description="Coding assistance",
            instructions="Write code.",
            tools=["read_file", "write_file", "execute_python"],
        )

        assert len(skill.tools) == 3
        assert "read_file" in skill.tools
        assert "execute_python" in skill.tools

    def test_has_tool(self):
        """Test has_tool method."""
        skill = Skill(
            id="test",
            name="Test",
            description="Test",
            instructions="Test",
            tools=["tool_a", "tool_b"],
        )

        assert skill.has_tool("tool_a") is True
        assert skill.has_tool("tool_b") is True
        assert skill.has_tool("tool_c") is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        skill = Skill(
            id="test",
            name="Test Skill",
            description="Description",
            instructions="Instructions",
            tools=["tool1"],
        )

        data = skill.to_dict()

        assert data["id"] == "test"
        assert data["name"] == "Test Skill"
        assert data["description"] == "Description"
        assert data["instructions"] == "Instructions"
        assert data["tools"] == ["tool1"]

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test",
            "name": "Test Skill",
            "description": "Description",
            "instructions": "Instructions",
            "tools": ["tool1", "tool2"],
        }

        skill = Skill.from_dict(data)

        assert skill.id == "test"
        assert skill.name == "Test Skill"
        assert skill.description == "Description"
        assert skill.instructions == "Instructions"
        assert skill.tools == ["tool1", "tool2"]

    def test_from_dict_without_tools(self):
        """Test deserialization without tools field."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "instructions": "Test",
        }

        skill = Skill.from_dict(data)

        assert skill.tools == []  # Default empty

    def test_str_representation(self):
        """Test string representation."""
        skill = Skill(
            id="test",
            name="Test Skill",
            description="Test",
            instructions="Test",
            tools=["tool1", "tool2"],
        )

        str_repr = str(skill)
        assert "test" in str_repr
        assert "Test Skill" in str_repr
        assert "2 tools" in str_repr

    def test_str_representation_no_tools(self):
        """Test string representation without tools."""
        skill = Skill(
            id="test",
            name="Test Skill",
            description="Test",
            instructions="Test",
        )

        str_repr = str(skill)
        assert "test" in str_repr
        assert "Test Skill" in str_repr
        assert "tools" not in str_repr  # No tools mentioned
