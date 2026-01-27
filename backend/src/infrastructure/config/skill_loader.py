"""
Skill Loader.

Loads skills from SKILL.md files with YAML frontmatter.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ...domain.entities.skill import Skill
from .gating import check_skill_requirements


class SkillLoader:
    """
    Loads skills from filesystem.

    Skills are stored as directories containing a SKILL.md file with
    YAML frontmatter and markdown instructions.
    """

    def __init__(self, skills_dir: Path | str) -> None:
        """
        Initialize skill loader.

        Args:
            skills_dir: Path to directory containing skill folders.
        """
        self.skills_dir = Path(skills_dir)

    def load_skill(
        self,
        skill_id: str,
        check_gating: bool = False,
    ) -> Skill | None:
        """
        Load a single skill by ID.

        Args:
            skill_id: Skill identifier (folder name).
            check_gating: If True, skip skill if prerequisites not met.

        Returns:
            Skill instance or None if not found or gating failed.
        """
        skill_path = self.skills_dir / skill_id / "SKILL.md"
        if not skill_path.exists():
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")
            skill = self._parse_skill_md(skill_id, content)
            
            # Check gating requirements
            if check_gating:
                result = check_skill_requirements(skill.metadata)
                if not result.passed:
                    print(f"[GATE] Skill '{skill_id}' skipped: {result.reason}")
                    return None
            
            return skill
        except Exception as e:
            raise ValueError(f"Failed to load skill '{skill_id}': {e}") from e

    def load_all_skills(self, check_gating: bool = False) -> list[Skill]:
        """
        Load all available skills.

        Args:
            check_gating: If True, skip skills with unmet prerequisites.

        Returns:
            List of Skill instances.
        """
        if not self.skills_dir.exists():
            return []

        skills = []
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                skill = self.load_skill(skill_dir.name, check_gating=check_gating)
                if skill:
                    skills.append(skill)
            except Exception:
                # Skip invalid skills
                continue

        return skills

    def _parse_skill_md(self, skill_id: str, content: str) -> Skill:
        """
        Parse SKILL.md content with YAML frontmatter.

        Expected format:
        ---
        name: Skill Name
        description: Short description
        tools:
          - tool1
          - tool2
        ---
        # Markdown instructions...

        Args:
            skill_id: Skill identifier.
            content: SKILL.md file content.

        Returns:
            Skill instance.

        Raises:
            ValueError: If frontmatter is invalid or missing required fields.
        """
        # Extract frontmatter between --- markers
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            raise ValueError(
                f"Invalid SKILL.md format for '{skill_id}': "
                "Missing YAML frontmatter (--- ... ---)"
            )

        frontmatter_text = match.group(1)
        instructions = match.group(2).strip()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML frontmatter in '{skill_id}': {e}"
            ) from e

        if not isinstance(frontmatter, dict):
            raise ValueError(
                f"Frontmatter must be a YAML object in '{skill_id}'"
            )

        # Extract required fields
        name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not name:
            raise ValueError(f"Missing 'name' in frontmatter for '{skill_id}'")
        if not description:
            raise ValueError(
                f"Missing 'description' in frontmatter for '{skill_id}'"
            )

        # Extract optional tools field
        tools = frontmatter.get("tools", [])
        if not isinstance(tools, list):
            raise ValueError(
                f"'tools' must be a list in frontmatter for '{skill_id}'"
            )

        # Extract optional version (default: 1.0.0)
        version = frontmatter.get("version", "1.0.0")
        if not isinstance(version, str):
            version = str(version)

        # Extract optional metadata for gating
        metadata = frontmatter.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return Skill(
            id=skill_id,
            name=name,
            description=description,
            instructions=instructions,
            version=version,
            tools=tools,
            metadata=metadata,
        )

    def get_skill_ids(self) -> list[str]:
        """
        Get list of available skill IDs.

        Returns:
            List of skill IDs (folder names).
        """
        if not self.skills_dir.exists():
            return []

        skill_ids = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skill_ids.append(skill_dir.name)

        return sorted(skill_ids)
