"""
Skill Importer.

Imports skills from external sources (Git repositories).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ...domain.entities.skill import Skill
from .skill_loader import SkillLoader

logger = logging.getLogger(__name__)


class SkillImporter:
    """Imports skills from Git repositories."""

    def __init__(self, local_skills_dir: Path | str) -> None:
        """
        Initialize importer.

        Args:
            local_skills_dir: Directory where skills will be installed.
        """
        self.local_skills_dir = Path(local_skills_dir)
        self.loader = SkillLoader(self.local_skills_dir)

    def import_from_git(self, repo_url: str, branch: Optional[str] = None) -> Skill:
        """
        Import a skill from a Git repository.

        Expected structure in Repo:
        - Root contains SKILL.md
        - OR Root contains a folder matching repo name with SKILL.md
        - If missing, auto-generates a default SKILL.md

        Args:
            repo_url: URL of the git repository.
            branch: Optional branch to checkout.

        Returns:
            Imported Skill instance.

        Raises:
            ValueError: If validation fails.
            RuntimeError: If git operation fails.
        """
        self._validate_repo_url(repo_url)
        
        # Extract skill ID from valid URL (e.g., github.com/user/my-skill -> my-skill)
        skill_id = self._extract_skill_id(repo_url)
        
        target_dir = self.local_skills_dir / skill_id
        if target_dir.exists():
            raise ValueError(f"Skill '{skill_id}' already exists at {target_dir}")

        logger.info(f"Starting import for skill '{skill_id}' from {repo_url}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Clone repo
            self._clone_repo(repo_url, temp_path, branch)
            
            # Locate SKILL.md
            skill_md, source_path = self._locate_or_create_skill_md(temp_path, skill_id, repo_url)

            # Validate by parsing (dry run)
            try:
                content = skill_md.read_text(encoding="utf-8")
                self.loader._parse_skill_md(skill_id, content)
            except Exception as e:
                logger.error(f"Failed to parse SKILL.md for {skill_id}: {e}")
                raise ValueError(f"Invalid SKILL.md in repository: {e}") from e
            
            # Install (Copy files)
            logger.info(f"Installing skill to {target_dir}...")
            target_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                self._copy_files(source_path, target_dir)
            except Exception as e:
                # Cleanup if copy fails (though target_dir was just created)
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                raise RuntimeError(f"Failed to install skill files: {e}") from e
            
            # Load installed skill
            logger.info(f"Successfully imported skill '{skill_id}'")
            return self.loader.load_skill(skill_id)

    def _validate_repo_url(self, url: str) -> None:
        """Validate repository URL format."""
        if not url:
            raise ValueError("Repository URL cannot be empty")
        
        # Basic protocol check
        valid_protocols = ("http://", "https://", "git@", "ssh://")
        if not url.startswith(valid_protocols):
            raise ValueError(f"Invalid repository URL protocol. Must start with one of: {valid_protocols}")

    def _locate_or_create_skill_md(self, base_path: Path, skill_id: str, repo_url: str) -> tuple[Path, Path]:
        """
        Find SKILL.md in the cloned repo, or create a default one.
        Returns: (path_to_skill_md, source_directory_to_copy)
        """
        # Strategy 1: In root
        if (base_path / "SKILL.md").exists():
            return base_path / "SKILL.md", base_path
            
        # Strategy 2: In subfolder matching skill_id
        if (base_path / skill_id / "SKILL.md").exists():
            return base_path / skill_id / "SKILL.md", base_path / skill_id
            
        # Strategy 3: Auto-create minimal SKILL.md if missing
        logger.warning(f"No SKILL.md found for '{skill_id}'. Auto-generating default configuration.")
        
        skill_md = base_path / "SKILL.md"
        self._generate_default_skill_md(skill_md, skill_id, repo_url)
        
        if not skill_md.exists():
             raise RuntimeError(f"Failed to generate SKILL.md at {skill_md}")
             
        return skill_md, base_path

    def _generate_default_skill_md(self, path: Path, skill_id: str, repo_url: str) -> None:
        """Generate a default SKILL.md content."""
        content = f"""---
name: {skill_id}
description: Auto-imported from {repo_url}
version: 0.1.0
metadata:
  created_at: {self._get_current_timestamp()}
  source_url: {repo_url}
---
# {skill_id}

This skill was automatically imported from a Git repository.
"""
        path.write_text(content, encoding="utf-8")

    def _get_current_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def _extract_skill_id(self, url: str) -> str:
        """Extract skill ID from URL (last path segment without .git)."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path.split("/")[-1] or "unknown_skill"

    def _clone_repo(self, url: str, path: Path, branch: Optional[str]) -> None:
        """Run git clone."""
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([url, str(path)])
        
        logger.debug(f"Executing git clone: {' '.join(cmd)}")
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone error: {e.stderr}")
            raise RuntimeError(f"Git clone failed: {e.stderr}") from e

    def _copy_files(self, src: Path, dst: Path) -> None:
        """Copy files ignoring .git directory."""
        def ignore_patterns(path, names):
            return {".git", "__pycache__", ".github", ".idea", ".vscode"}

        # Note: dst is assumed to rely on shutil.copytree creating it or handle existing
        # But here we used dirs_exist_ok=True to allow merging if needed (though we check exists before)
        shutil.copytree(src, dst, ignore=ignore_patterns, dirs_exist_ok=True)
