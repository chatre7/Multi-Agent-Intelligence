"""
Unit tests for SkillMarketplace.
"""

import json
import shutil
from pathlib import Path

import pytest

from src.infrastructure.config.skill_marketplace import SkillMarketplace


class TestSkillMarketplace:
    """Test SkillMarketplace functionality."""

    @pytest.fixture
    def registry_setup(self, tmp_path):
        """Setup a fake local registry."""
        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        
        # Create a test skill source
        skill_src = registry_dir / "skills" / "data-science" / "v1.0.0"
        skill_src.mkdir(parents=True)
        (skill_src / "SKILL.md").write_text(
            """---
name: Data Science
description: Data analysis tools
version: 1.0.0
tags: [data, python]
---
# Data Science
Instructions...
""",
            encoding="utf-8"
        )
        (skill_src / "sometool.py").write_text("print('hello')", encoding="utf-8")

        # Create registry index
        index = {
            "skills": {
                "data-science": {
                    "name": "Data Science",
                    "description": "Data analysis tools",
                    "latest": "1.0.0",
                    "versions": {
                        "1.0.0": {
                            "url": str(skill_src)  # Points to local dir
                        }
                    },
                    "tags": ["data", "python"],
                    "author": "tester"
                }
            }
        }
        
        index_file = registry_dir / "index.json"
        index_file.write_text(json.dumps(index), encoding="utf-8")
        
        return index_file

    def test_list_available_skills(self, registry_setup, tmp_path):
        """Test listing skills."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        skills = marketplace.list_available_skills()
        
        assert len(skills) == 1
        assert skills[0].id == "data-science"
        assert skills[0].latest_version == "1.0.0"
        assert "data" in skills[0].tags

    def test_search_skills(self, registry_setup, tmp_path):
        """Test searching skills."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        
        # Match by name
        results = marketplace.search_skills("Data")
        assert len(results) == 1
        
        # Match by tag
        results = marketplace.search_skills("python")
        assert len(results) == 1
        
        # No match
        results = marketplace.search_skills("java")
        assert len(results) == 0

    def test_install_skill(self, registry_setup, tmp_path):
        """Test installing a skill."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        
        # Install
        skill = marketplace.install_skill("data-science")
        
        assert skill.id == "data-science"
        assert skill.version == "1.0.0"
        
        # Check files existed
        installed_path = local_dir / "data-science"
        assert installed_path.exists()
        assert (installed_path / "SKILL.md").exists()
        assert (installed_path / "sometool.py").exists()

    def test_install_skill_not_found(self, registry_setup, tmp_path):
        """Test installing missing skill."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        
        with pytest.raises(ValueError, match="not found"):
            marketplace.install_skill("unknown-skill")

    def test_install_already_exists_no_force(self, registry_setup, tmp_path):
        """Test installing existing skill without force."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        
        # Install first time
        marketplace.install_skill("data-science")
        
        # Install second time (should just return existing)
        skill = marketplace.install_skill("data-science")
        assert skill.id == "data-science"

    def test_install_already_exists_with_force(self, registry_setup, tmp_path):
        """Test installing existing skill with force."""
        local_dir = tmp_path / "installed_skills"
        local_dir.mkdir()
        marketplace = SkillMarketplace(str(registry_setup), local_dir)
        
        # Install first time
        marketplace.install_skill("data-science")
        
        # Modify file to prove overwrite
        (local_dir / "data-science" / "extra.txt").write_text("modified")
        
        # Install second time with force
        marketplace.install_skill("data-science", force=True)
        
        # Extra file should be gone (directory was cleaned)
        assert not (local_dir / "data-science" / "extra.txt").exists()
