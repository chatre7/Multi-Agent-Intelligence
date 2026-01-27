"""
Unit tests for version utilities.
"""

import pytest

from src.domain.value_objects.version_utils import (
    SemanticVersion,
    parse_version,
    parse_skill_ref,
    satisfies_version,
    get_latest_version,
)


class TestSemanticVersion:
    """Test SemanticVersion dataclass."""

    def test_str_representation(self):
        """Test string representation."""
        v = SemanticVersion(1, 2, 3)
        assert str(v) == "1.2.3"

    def test_str_with_prerelease(self):
        """Test string with prerelease."""
        v = SemanticVersion(1, 2, 3, "beta.1")
        assert str(v) == "1.2.3-beta.1"

    def test_comparison_major(self):
        """Test major version comparison."""
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(2, 0, 0)
        assert v1 < v2
        assert v2 > v1

    def test_comparison_minor(self):
        """Test minor version comparison."""
        v1 = SemanticVersion(1, 1, 0)
        v2 = SemanticVersion(1, 2, 0)
        assert v1 < v2

    def test_comparison_patch(self):
        """Test patch version comparison."""
        v1 = SemanticVersion(1, 2, 3)
        v2 = SemanticVersion(1, 2, 4)
        assert v1 < v2

    def test_comparison_prerelease(self):
        """Test prerelease is less than release."""
        v1 = SemanticVersion(1, 0, 0, "alpha")
        v2 = SemanticVersion(1, 0, 0)
        assert v1 < v2

    def test_equality(self):
        """Test version equality."""
        v1 = SemanticVersion(1, 2, 3)
        v2 = SemanticVersion(1, 2, 3)
        assert v1 == v2


class TestParseVersion:
    """Test parse_version function."""

    def test_simple_version(self):
        """Test parsing simple version."""
        v = parse_version("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_prerelease_version(self):
        """Test parsing prerelease version."""
        v = parse_version("2.0.0-beta.1")
        assert v.major == 2
        assert v.prerelease == "beta.1"

    def test_invalid_version(self):
        """Test invalid version raises error."""
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("invalid")

    def test_partial_version(self):
        """Test partial version raises error."""
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("1.2")


class TestParseSkillRef:
    """Test parse_skill_ref function."""

    def test_simple_ref(self):
        """Test parsing simple skill reference."""
        skill_id, constraint = parse_skill_ref("python-engineering")
        assert skill_id == "python-engineering"
        assert constraint is None

    def test_ref_with_version(self):
        """Test parsing reference with exact version."""
        skill_id, constraint = parse_skill_ref("python-engineering@1.2.0")
        assert skill_id == "python-engineering"
        assert constraint == "1.2.0"

    def test_ref_with_caret(self):
        """Test parsing reference with caret constraint."""
        skill_id, constraint = parse_skill_ref("skill@^1.0.0")
        assert skill_id == "skill"
        assert constraint == "^1.0.0"

    def test_ref_with_tilde(self):
        """Test parsing reference with tilde constraint."""
        skill_id, constraint = parse_skill_ref("skill@~2.1")
        assert skill_id == "skill"
        assert constraint == "~2.1"


class TestSatisfiesVersion:
    """Test satisfies_version function."""

    def test_none_constraint(self):
        """Test None constraint matches any version."""
        assert satisfies_version("1.2.3", None) is True

    def test_latest_constraint(self):
        """Test 'latest' constraint matches any version."""
        assert satisfies_version("1.2.3", "latest") is True

    def test_exact_match(self):
        """Test exact version match."""
        assert satisfies_version("1.2.3", "1.2.3") is True
        assert satisfies_version("1.2.3", "1.2.4") is False

    def test_caret_constraint(self):
        """Test caret constraint (^1.2.3 = compatible with 1.x.x)."""
        # Same major, higher minor/patch - OK
        assert satisfies_version("1.5.0", "^1.2.3") is True
        # Same major, same version - OK
        assert satisfies_version("1.2.3", "^1.2.3") is True
        # Same major, lower - NOT OK
        assert satisfies_version("1.1.0", "^1.2.3") is False
        # Different major - NOT OK
        assert satisfies_version("2.0.0", "^1.2.3") is False

    def test_tilde_constraint(self):
        """Test tilde constraint (~1.2.3 = compatible with 1.2.x)."""
        # Same major.minor, higher patch - OK
        assert satisfies_version("1.2.5", "~1.2.3") is True
        # Same - OK
        assert satisfies_version("1.2.3", "~1.2.3") is True
        # Different minor - NOT OK
        assert satisfies_version("1.3.0", "~1.2.3") is False

    def test_greater_equal(self):
        """Test >= constraint."""
        assert satisfies_version("1.5.0", ">=1.2.0") is True
        assert satisfies_version("1.2.0", ">=1.2.0") is True
        assert satisfies_version("1.1.0", ">=1.2.0") is False

    def test_greater_than(self):
        """Test > constraint."""
        assert satisfies_version("1.5.0", ">1.2.0") is True
        assert satisfies_version("1.2.0", ">1.2.0") is False

    def test_less_equal(self):
        """Test <= constraint."""
        assert satisfies_version("1.0.0", "<=1.2.0") is True
        assert satisfies_version("1.2.0", "<=1.2.0") is True
        assert satisfies_version("1.3.0", "<=1.2.0") is False

    def test_less_than(self):
        """Test < constraint."""
        assert satisfies_version("1.0.0", "<1.2.0") is True
        assert satisfies_version("1.2.0", "<1.2.0") is False


class TestGetLatestVersion:
    """Test get_latest_version function."""

    def test_empty_list(self):
        """Test empty list returns None."""
        assert get_latest_version([]) is None

    def test_single_version(self):
        """Test single version returns itself."""
        assert get_latest_version(["1.0.0"]) == "1.0.0"

    def test_multiple_versions(self):
        """Test finding latest from multiple versions."""
        versions = ["1.0.0", "2.0.0", "1.5.0", "2.1.0"]
        assert get_latest_version(versions) == "2.1.0"

    def test_with_prerelease(self):
        """Test prerelease is less than release."""
        versions = ["1.0.0", "1.0.0-beta", "0.9.0"]
        assert get_latest_version(versions) == "1.0.0"

    def test_skips_invalid(self):
        """Test invalid versions are skipped."""
        versions = ["1.0.0", "invalid", "2.0.0"]
        assert get_latest_version(versions) == "2.0.0"
