"""
Skill Entity.

Represents a reusable skill that can be assigned to agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    """
    Skill Entity - represents a reusable capability.

    Skills are optional packages of knowledge and tools that can be
    assigned to agents to enhance their capabilities.

    Attributes:
        id: Unique identifier for the skill (e.g., "python-engineering").
        name: Human-readable name.
        description: Short description of what the skill provides.
        instructions: Full markdown instructions for the skill.
        version: Semantic version string (e.g., "1.2.0").
        tools: Optional list of tool IDs this skill provides.
        metadata: Optional metadata for gating and other config.
    """

    # Required fields
    id: str
    name: str
    description: str
    instructions: str

    # Optional fields with defaults
    version: str = "1.0.0"
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_tool(self, tool_id: str) -> bool:
        """
        Check if skill provides a specific tool.

        Args:
            tool_id: The tool ID to check.

        Returns:
            True if skill provides the tool.
        """
        return tool_id in self.tools

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize skill to dictionary.

        Returns:
            Dictionary representation of the skill.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "version": self.version,
            "tools": self.tools.copy(),
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skill:
        """
        Deserialize skill from dictionary.

        Args:
            data: Dictionary containing skill data.

        Returns:
            Skill instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            version=data.get("version", "1.0.0"),
            tools=data.get("tools", []),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation."""
        tools_info = f" ({len(self.tools)} tools)" if self.tools else ""
        return f"Skill({self.id}@{self.version}: {self.name}{tools_info})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Skill(id='{self.id}', name='{self.name}', tools={len(self.tools)})"
