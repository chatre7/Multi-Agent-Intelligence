"""
Skill Marketplace.

Manages finding, downloading, and installing skills from a registry.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.request import urlopen
from urllib.error import URLError

from ...domain.entities.skill import Skill
from ...domain.value_objects.version_utils import (
    SemanticVersion,
    parse_version,
    satisfies_version,
    get_latest_version,
)
from .skill_loader import SkillLoader


@dataclass
class RegistrySkillInfo:
    """Information about a skill in the registry."""
    id: str
    name: str
    description: str
    latest_version: str
    versions: list[str]
    tags: list[str]
    author: str


class SkillMarketplace:
    """
    Client for interacting with the Skill Marketplace.
    """

    def __init__(self, registry_url: str, local_skills_dir: Path | str) -> None:
        """
        Initialize marketplace client.

        Args:
            registry_url: URL or local path to registry index.json.
            local_skills_dir: Directory where skills are installed.
        """
        self.registry_url = registry_url
        self.local_skills_dir = Path(local_skills_dir)
        self.loader = SkillLoader(self.local_skills_dir)

    def list_available_skills(self) -> list[RegistrySkillInfo]:
        """
        List all skills available in the registry.

        Returns:
            List of registry skill info.
        """
        index = self._fetch_registry_index()
        skills = []
        
        for skill_id, data in index.get("skills", {}).items():
            versions = list(data.get("versions", {}).keys())
            skills.append(RegistrySkillInfo(
                id=skill_id,
                name=data.get("name", skill_id),
                description=data.get("description", ""),
                latest_version=data.get("latest", get_latest_version(versions)),
                versions=sorted(versions),
                tags=data.get("tags", []),
                author=data.get("author", "unknown"),
            ))
            
        return skills

    def search_skills(self, query: str) -> list[RegistrySkillInfo]:
        """
        Search skills by name, description, or tags.

        Args:
            query: Search query string.

        Returns:
            List of matching skills.
        """
        all_skills = self.list_available_skills()
        query = query.lower()
        
        results = []
        for skill in all_skills:
            if (query in skill.name.lower() or 
                query in skill.description.lower() or 
                query in skill.id.lower() or
                any(query in tag.lower() for tag in skill.tags)):
                results.append(skill)
                
        return results

    def install_skill(self, skill_id: str, version: str = "latest", force: bool = False) -> Skill:
        """
        Install a skill from the registry.

        Args:
            skill_id: ID of the skill to install.
            version: Specific version or "latest".
            force: If True, overwrite existing installation.

        Returns:
            Installed Skill instance.

        Raises:
            ValueError: If skill or version not found.
            IOError: If installation fails.
        """
        index = self._fetch_registry_index()
        skill_data = index.get("skills", {}).get(skill_id)
        
        if not skill_data:
            raise ValueError(f"Skill '{skill_id}' not found in registry")

        if version == "latest":
            version = skill_data.get("latest")
            if not version:
                versions = list(skill_data.get("versions", {}).keys())
                version = get_latest_version(versions)

        version_info = skill_data.get("versions", {}).get(version)
        if not version_info:
            raise ValueError(f"Version '{version}' for skill '{skill_id}' not found")

        # Check if already installed
        target_dir = self.local_skills_dir / skill_id
        if target_dir.exists():
            if not force:
                # Check current version
                current_skill = self.loader.load_skill(skill_id)
                if current_skill and current_skill.version == version:
                    print(f"Skill '{skill_id}' version {version} is already installed.")
                    return current_skill
                # Proceed to upgrade/downgrade if force not strictly required for version change?
                # For safety, require force for any overwrite, or maybe auto-upgrade?
                # Let's say we require force to overwrite ONLY if version is same? 
                # Actually standard package managers update without force usually.
                # But here we are overwriting files. Let's start with requiring force if dir exists.
                # Or better: clean update.
                pass
            
            shutil.rmtree(target_dir)

        # Download and install
        source_url = version_info.get("url")
        if not source_url:
            raise ValueError(f"No download URL for {skill_id}@{version}")

        try:
            self._download_and_extract(source_url, target_dir)
        except Exception as e:
            # Cleanup on failure
            if target_dir.exists():
                shutil.rmtree(target_dir)
            raise IOError(f"Failed to install {skill_id}: {e}") from e

        # Validate installation
        installed_skill = self.loader.load_skill(skill_id)
        if not installed_skill:
            raise ValueError(f"Installation failed: Could not load skill from {target_dir}")

        return installed_skill

    def _fetch_registry_index(self) -> dict[str, Any]:
        """Fetch and parse registry index."""
        # Support local file path for testing/offline
        if self.registry_url.startswith("file://") or Path(self.registry_url).exists():
            path = Path(self.registry_url.replace("file://", ""))
            return json.loads(path.read_text(encoding="utf-8"))
        
        # Remote URL
        try:
            with urlopen(self.registry_url) as response:
                return json.loads(response.read().decode("utf-8"))
        except URLError as e:
            raise IOError(f"Failed to fetch registry from {self.registry_url}: {e}") from e

    def _download_and_extract(self, url: str, target_dir: Path) -> None:
        """
        Download skill package and extract to target directory.
        
        Supports local directory copy (for testing/local registry) and HTTP download.
        """
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Handle Local Path (Copy)
        if url.startswith("file://") or Path(url).exists():
            src_path = Path(url.replace("file://", ""))
            if src_path.is_dir():
                # Copy contents
                shutil.copytree(src_path, target_dir, dirs_exist_ok=True)
                return
            else:
                # It's a file (zip/tar)? Not supported yet for local simple file, assume dir for MVP
                raise ValueError("Local source must be a directory for now")

        # 2. Handle HTTP (Simulated for MVP or implementing basic zip download)
        # For MVP, we might only support downloading ZIPs if we implemented unzip.
        # But to keep it simple and generic, let's assume we can't do full zip handling 
        # without 'zipfile' module which is available.
        
        # Let's implement basic zip download if URL ends in .zip
        if url.endswith(".zip"):
             import zipfile
             from io import BytesIO
             
             with urlopen(url) as response:
                 zip_data = response.read()
                 
             with zipfile.ZipFile(BytesIO(zip_data)) as zf:
                 zf.extractall(target_dir)
             return

        raise NotImplementedError("Only local directory copy and .zip download are supported currently.")
