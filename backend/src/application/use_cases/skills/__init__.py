"""
Skill Use Cases.

Functions for working with agent skills.
"""

from __future__ import annotations

from src.domain.entities.agent import Agent
from src.domain.entities.skill import Skill


def get_effective_system_prompt(agent: Agent, skills: list[Skill]) -> str:
    """
    Combine agent's system prompt with skill instructions.

    Args:
        agent: The agent.
        skills: List of skills assigned to the agent.

    Returns:
        Combined system prompt with skill instructions.
    """
    if not skills:
        return agent.system_prompt

    parts = [agent.system_prompt]

    for skill in skills:
        parts.append(f"\n\n## Skill: {skill.name}\n\n{skill.instructions}")

    return "\n".join(parts)


def get_effective_tools(agent: Agent, skills: list[Skill]) -> list[str]:
    """
    Combine agent's tools with skill tools.

    Args:
        agent: The agent.
        skills: List of skills assigned to the agent.

    Returns:
        Combined list of tool IDs (deduplicated).
    """
    all_tools = set(agent.tools)

    for skill in skills:
        all_tools.update(skill.tools)

    return list(all_tools)
