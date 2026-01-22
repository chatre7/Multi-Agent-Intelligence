"""
SemanticVersion Value Object.

Implements semantic versioning (SemVer) with comparison and increment operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(frozen=True)
class SemanticVersion:
    """
    Immutable semantic version value object.

    Follows SemVer specification: MAJOR.MINOR.PATCH

    Attributes:
        major: Major version number (breaking changes).
        minor: Minor version number (new features, backward compatible).
        patch: Patch version number (bug fixes).
    """

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        """Validate version components are non-negative."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version components must be non-negative integers")

    @classmethod
    def from_string(cls, version_string: str) -> SemanticVersion:
        """
        Parse version from string.

        Args:
            version_string: Version string in format "MAJOR.MINOR.PATCH".

        Returns:
            SemanticVersion instance.

        Raises:
            ValueError: If string format is invalid.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        match = re.match(pattern, version_string.strip())

        if not match:
            raise ValueError(
                f"Invalid version format: '{version_string}'. "
                "Expected format: MAJOR.MINOR.PATCH (e.g., '1.2.3')"
            )

        major, minor, patch = map(int, match.groups())
        return cls(major=major, minor=minor, patch=patch)

    def to_tuple(self) -> tuple[int, int, int]:
        """
        Convert to tuple for comparison.

        Returns:
            Tuple of (major, minor, patch).
        """
        return (self.major, self.minor, self.patch)

    def increment_patch(self) -> SemanticVersion:
        """
        Create new version with incremented patch.

        Returns:
            New SemanticVersion with patch + 1.
        """
        return SemanticVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
        )

    def increment_minor(self) -> SemanticVersion:
        """
        Create new version with incremented minor and reset patch.

        Returns:
            New SemanticVersion with minor + 1, patch = 0.
        """
        return SemanticVersion(
            major=self.major,
            minor=self.minor + 1,
            patch=0,
        )

    def increment_major(self) -> SemanticVersion:
        """
        Create new version with incremented major and reset minor/patch.

        Returns:
            New SemanticVersion with major + 1, minor = 0, patch = 0.
        """
        return SemanticVersion(
            major=self.major + 1,
            minor=0,
            patch=0,
        )

    def is_compatible_with(self, other: SemanticVersion) -> bool:
        """
        Check if this version is backward compatible with another.

        Two versions are compatible if they have the same major version.

        Args:
            other: Version to compare with.

        Returns:
            True if versions are compatible.
        """
        return self.major == other.major

    def __str__(self) -> str:
        """String representation in SemVer format."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"SemanticVersion({self.major}, {self.minor}, {self.patch})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another version."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self.to_tuple() == other.to_tuple()

    def __lt__(self, other: SemanticVersion) -> bool:
        """Check if this version is less than another."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self.to_tuple() < other.to_tuple()

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.to_tuple())
