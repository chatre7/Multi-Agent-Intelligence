"""
Version utilities for skill versioning.

Provides semver parsing and version constraint matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SemanticVersion:
    """
    Parsed semantic version.
    
    Format: MAJOR.MINOR.PATCH[-PRERELEASE]
    """
    
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    
    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base
    
    def __lt__(self, other: SemanticVersion) -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # Prerelease versions are less than release
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return self.prerelease < other.prerelease
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )
    
    def __le__(self, other: SemanticVersion) -> bool:
        return self == other or self < other
    
    def __gt__(self, other: SemanticVersion) -> bool:
        return not self <= other
    
    def __ge__(self, other: SemanticVersion) -> bool:
        return not self < other


VERSION_PATTERN = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$"
)


def parse_version(version_str: str) -> SemanticVersion:
    """
    Parse a semantic version string.
    
    Args:
        version_str: Version string like "1.2.3" or "1.2.3-beta.1"
        
    Returns:
        SemanticVersion instance.
        
    Raises:
        ValueError: If version string is invalid.
    """
    version_str = version_str.strip()
    match = VERSION_PATTERN.match(version_str)
    
    if not match:
        raise ValueError(f"Invalid version format: '{version_str}'")
    
    major, minor, patch, prerelease = match.groups()
    return SemanticVersion(
        major=int(major),
        minor=int(minor),
        patch=int(patch),
        prerelease=prerelease or "",
    )


def parse_skill_ref(skill_ref: str) -> Tuple[str, str | None]:
    """
    Parse a skill reference with optional version constraint.
    
    Formats:
        - "skill-id" → (skill-id, None)
        - "skill-id@1.0.0" → (skill-id, "1.0.0")
        - "skill-id@^1.0.0" → (skill-id, "^1.0.0")
        - "skill-id@~2.1" → (skill-id, "~2.1")
    
    Args:
        skill_ref: Skill reference string.
        
    Returns:
        Tuple of (skill_id, version_constraint).
    """
    if "@" not in skill_ref:
        return (skill_ref, None)
    
    parts = skill_ref.split("@", 1)
    return (parts[0], parts[1])


def satisfies_version(version: str, constraint: str | None) -> bool:
    """
    Check if a version satisfies a version constraint.
    
    Constraint formats:
        - None or "latest" → matches any version
        - "1.2.3" → exact match
        - "^1.2.3" → compatible with 1.x.x (major must match)
        - "~1.2.3" → compatible with 1.2.x (major.minor must match)
        - ">=1.2.0" → greater than or equal
        - ">1.2.0" → greater than
        - "<=1.2.0" → less than or equal
        - "<1.2.0" → less than
        
    Args:
        version: The actual version string.
        constraint: The version constraint.
        
    Returns:
        True if version satisfies constraint.
    """
    if constraint is None or constraint.lower() in ["latest", "*"]:
        return True
    
    constraint = constraint.strip()
    
    try:
        actual = parse_version(version)
    except ValueError:
        return False
    
    # Caret: ^1.2.3 means >=1.2.3 and <2.0.0
    if constraint.startswith("^"):
        try:
            target = parse_version(constraint[1:])
        except ValueError:
            # Try partial version like ^1.2
            parts = constraint[1:].split(".")
            if len(parts) == 2:
                target = SemanticVersion(int(parts[0]), int(parts[1]), 0)
            else:
                return False
        
        # Must have same major version
        if actual.major != target.major:
            return False
        # Must be >= target
        return actual >= target
    
    # Tilde: ~1.2.3 means >=1.2.3 and <1.3.0
    if constraint.startswith("~"):
        try:
            target = parse_version(constraint[1:])
        except ValueError:
            # Try partial version like ~1.2
            parts = constraint[1:].split(".")
            if len(parts) == 2:
                target = SemanticVersion(int(parts[0]), int(parts[1]), 0)
            else:
                return False
        
        # Must have same major and minor
        if actual.major != target.major or actual.minor != target.minor:
            return False
        # Must be >= target patch
        return actual >= target
    
    # Range operators
    if constraint.startswith(">="):
        target = parse_version(constraint[2:])
        return actual >= target
    
    if constraint.startswith(">"):
        target = parse_version(constraint[1:])
        return actual > target
    
    if constraint.startswith("<="):
        target = parse_version(constraint[2:])
        return actual <= target
    
    if constraint.startswith("<"):
        target = parse_version(constraint[1:])
        return actual < target
    
    # Exact match
    try:
        target = parse_version(constraint)
        return actual == target
    except ValueError:
        return False


def get_latest_version(versions: list[str]) -> str | None:
    """
    Get the latest version from a list of version strings.
    
    Args:
        versions: List of version strings.
        
    Returns:
        Latest version string, or None if list is empty.
    """
    if not versions:
        return None
    
    parsed = []
    for v in versions:
        try:
            parsed.append((parse_version(v), v))
        except ValueError:
            continue
    
    if not parsed:
        return None
    
    # Sort descending and return the first
    parsed.sort(key=lambda x: x[0], reverse=True)
    return parsed[0][1]
