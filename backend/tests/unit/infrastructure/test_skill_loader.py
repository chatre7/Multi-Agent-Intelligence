"""
Unit tests for SkillLoader.
"""

import pytest
from pathlib import Path

from src.infrastructure.config.skill_loader import SkillLoader


class TestSkillLoader:
    """Test SkillLoader functionality."""

    def test_load_skill_valid(self, tmp_path):
        """Test loading a valid skill."""
        # Create a test skill
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Test Skill
description: A test skill for unit testing
tools:
  - read_file
  - write_file
---

# Test Skill Instructions

This is a test skill.
Use it for testing purposes.
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        skill = loader.load_skill("test-skill")

        assert skill is not None
        assert skill.id == "test-skill"
        assert skill.name == "Test Skill"
        assert skill.description == "A test skill for unit testing"
        assert "Test Skill Instructions" in skill.instructions
        assert skill.tools == ["read_file", "write_file"]

    def test_load_skill_without_tools(self, tmp_path):
        """Test loading a skill without tools field."""
        skill_dir = tmp_path / "simple-skill"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Simple Skill
description: No tools needed
---

# Simple Instructions

Just instructions, no tools.
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        skill = loader.load_skill("simple-skill")

        assert skill is not None
        assert skill.tools == []  # No tools

    def test_load_skill_not_found(self, tmp_path):
        """Test loading a non-existent skill."""
        loader = SkillLoader(tmp_path)
        skill = loader.load_skill("nonexistent")

        assert skill is None

    def test_load_skill_invalid_frontmatter(self, tmp_path):
        """Test loading a skill with invalid YAML frontmatter."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Bad Skill
description: Missing closing marker

# This should fail
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        
        with pytest.raises(ValueError, match="Missing YAML frontmatter"):
            loader.load_skill("bad-skill")

    def test_load_skill_missing_name(self, tmp_path):
        """Test loading a skill without required 'name' field."""
        skill_dir = tmp_path / "no-name"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
description: Missing name field
---

# Instructions
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        
        with pytest.raises(ValueError, match="Missing 'name'"):
            loader.load_skill("no-name")

    def test_load_skill_missing_description(self, tmp_path):
        """Test loading a skill without required 'description' field."""
        skill_dir = tmp_path / "no-desc"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: No Description
---

# Instructions
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        
        with pytest.raises(ValueError, match="Missing 'description'"):
            loader.load_skill("no-desc")

    def test_load_all_skills(self, tmp_path):
        """Test loading all available skills."""
        # Create multiple skills
        for i in range(3):
            skill_dir = tmp_path / f"skill-{i}"
            skill_dir.mkdir()
            
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                f"""---
name: Skill {i}
description: Test skill {i}
---

# Skill {i}
""",
                encoding="utf-8",
            )

        loader = SkillLoader(tmp_path)
        skills = loader.load_all_skills()

        assert len(skills) == 3
        skill_ids = {s.id for s in skills}
        assert skill_ids == {"skill-0", "skill-1", "skill-2"}

    def test_load_all_skills_empty_directory(self, tmp_path):
        """Test loading skills from empty directory."""
        loader = SkillLoader(tmp_path)
        skills = loader.load_all_skills()

        assert skills == []

    def test_load_all_skills_skips_invalid(self, tmp_path):
        """Test that load_all_skills skips invalid skills."""
        # Valid skill
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "SKILL.md").write_text(
            """---
name: Valid
description: Valid skill
---

# Valid
""",
            encoding="utf-8",
        )

        # Invalid skill (missing name)
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "SKILL.md").write_text(
            """---
description: Invalid
---

# Invalid
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        skills = loader.load_all_skills()

        # Should only load valid skill
        assert len(skills) == 1
        assert skills[0].id == "valid"

    def test_get_skill_ids(self, tmp_path):
        """Test getting list of available skill IDs."""
        # Create skills
        for name in ["python", "javascript", "rust"]:
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"""---
name: {name.title()}
description: {name} skill
---

# {name}
""",
                encoding="utf-8",
            )

        loader = SkillLoader(tmp_path)
        skill_ids = loader.get_skill_ids()

        assert skill_ids == ["javascript", "python", "rust"]  # Sorted

    def test_load_skill_with_complex_instructions(self, tmp_path):
        """Test loading skill with complex markdown instructions."""
        skill_dir = tmp_path / "complex"
        skill_dir.mkdir()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Complex Skill
description: Skill with complex markdown
---

# Complex Instructions

## Section 1

- Item 1
- Item 2

## Section 2

```python
def example():
    return "code"
```

**Bold text** and *italic text*.
""",
            encoding="utf-8",
        )

        loader = SkillLoader(tmp_path)
        skill = loader.load_skill("complex")

        assert skill is not None
        assert "Section 1" in skill.instructions
        assert "Section 2" in skill.instructions
        assert "def example():" in skill.instructions
        assert "**Bold text**" in skill.instructions
