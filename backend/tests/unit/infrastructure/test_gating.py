"""
Unit tests for gating utilities.
"""

import os
from unittest.mock import patch

import pytest

from src.infrastructure.config.gating import (
    GatingResult,
    check_skill_requirements,
    binary_exists,
    get_current_os,
    check_binary_requirement,
    check_any_binary_requirement,
    check_env_requirement,
    check_os_requirement,
)


class TestGatingResult:
    """Test GatingResult dataclass."""

    def test_ok(self):
        """Test successful result."""
        result = GatingResult.ok()
        assert result.passed is True
        assert result.reason == ""

    def test_fail(self):
        """Test failed result."""
        result = GatingResult.fail("Missing python")
        assert result.passed is False
        assert result.reason == "Missing python"


class TestBinaryExists:
    """Test binary_exists function."""

    def test_python_exists(self):
        """Test that python binary exists."""
        # Python should exist on any system running tests
        assert binary_exists("python") or binary_exists("python3")

    def test_nonexistent_binary(self):
        """Test nonexistent binary."""
        assert binary_exists("this_binary_does_not_exist_12345") is False


class TestCheckBinaryRequirement:
    """Test check_binary_requirement function."""

    def test_existing_binaries(self):
        """Test with existing binaries."""
        # Git should exist on most dev systems
        with patch("src.infrastructure.config.gating.binary_exists", return_value=True):
            result = check_binary_requirement(["git", "python"])
            assert result.passed is True

    def test_missing_binary(self):
        """Test with missing binary."""
        with patch("src.infrastructure.config.gating.binary_exists", side_effect=lambda b: b != "missing"):
            result = check_binary_requirement(["python", "missing"])
            assert result.passed is False
            assert "missing" in result.reason.lower()


class TestCheckAnyBinaryRequirement:
    """Test check_any_binary_requirement function."""

    def test_empty_list(self):
        """Test empty list passes."""
        result = check_any_binary_requirement([])
        assert result.passed is True

    def test_one_exists(self):
        """Test passes if any binary exists."""
        with patch("src.infrastructure.config.gating.binary_exists", side_effect=lambda b: b == "npm"):
            result = check_any_binary_requirement(["npm", "yarn", "pnpm"])
            assert result.passed is True

    def test_none_exists(self):
        """Test fails if none exist."""
        with patch("src.infrastructure.config.gating.binary_exists", return_value=False):
            result = check_any_binary_requirement(["npm", "yarn"])
            assert result.passed is False


class TestCheckEnvRequirement:
    """Test check_env_requirement function."""

    def test_existing_env(self):
        """Test with existing env var."""
        with patch.dict(os.environ, {"MY_TEST_VAR": "value"}):
            result = check_env_requirement(["MY_TEST_VAR"])
            assert result.passed is True

    def test_missing_env(self):
        """Test with missing env var."""
        # Ensure var doesn't exist
        os.environ.pop("MISSING_VAR_12345", None)
        result = check_env_requirement(["MISSING_VAR_12345"])
        assert result.passed is False
        assert "MISSING_VAR_12345" in result.reason


class TestCheckOsRequirement:
    """Test check_os_requirement function."""

    def test_empty_list(self):
        """Test empty list allows any OS."""
        result = check_os_requirement([])
        assert result.passed is True

    def test_current_os_allowed(self):
        """Test current OS is allowed."""
        current = get_current_os()
        result = check_os_requirement([current])
        assert result.passed is True

    def test_current_os_not_allowed(self):
        """Test current OS not allowed."""
        # Use an OS that definitely isn't current
        fake_os = "fake_os_12345"
        result = check_os_requirement([fake_os])
        assert result.passed is False


class TestCheckSkillRequirements:
    """Test check_skill_requirements function."""

    def test_empty_metadata(self):
        """Test empty metadata passes."""
        result = check_skill_requirements({})
        assert result.passed is True

    def test_bins_requirement_pass(self):
        """Test bins requirement passes."""
        with patch("src.infrastructure.config.gating.binary_exists", return_value=True):
            result = check_skill_requirements({
                "requires": {"bins": ["python", "git"]}
            })
            assert result.passed is True

    def test_bins_requirement_fail(self):
        """Test bins requirement fails."""
        with patch("src.infrastructure.config.gating.binary_exists", return_value=False):
            result = check_skill_requirements({
                "requires": {"bins": ["nonexistent_binary"]}
            })
            assert result.passed is False
            assert "nonexistent_binary" in result.reason

    def test_env_requirement_pass(self):
        """Test env requirement passes."""
        with patch.dict(os.environ, {"MY_API_KEY": "secret"}):
            result = check_skill_requirements({
                "requires": {"env": ["MY_API_KEY"]}
            })
            assert result.passed is True

    def test_env_requirement_fail(self):
        """Test env requirement fails."""
        os.environ.pop("MISSING_KEY_12345", None)
        result = check_skill_requirements({
            "requires": {"env": ["MISSING_KEY_12345"]}
        })
        assert result.passed is False

    def test_os_requirement_pass(self):
        """Test OS requirement passes."""
        current = get_current_os()
        result = check_skill_requirements({
            "os": [current]
        })
        assert result.passed is True

    def test_os_requirement_fail(self):
        """Test OS requirement fails."""
        result = check_skill_requirements({
            "os": ["fake_os"]
        })
        assert result.passed is False

    def test_any_bins_requirement(self):
        """Test anyBins requirement."""
        with patch("src.infrastructure.config.gating.binary_exists", side_effect=lambda b: b == "npm"):
            result = check_skill_requirements({
                "requires": {"anyBins": ["npm", "yarn", "pnpm"]}
            })
            assert result.passed is True

    def test_combined_requirements(self):
        """Test multiple requirements together."""
        current_os = get_current_os()
        
        with patch("src.infrastructure.config.gating.binary_exists", return_value=True):
            with patch.dict(os.environ, {"TEST_KEY": "value"}):
                result = check_skill_requirements({
                    "requires": {
                        "bins": ["python"],
                        "env": ["TEST_KEY"],
                    },
                    "os": [current_os],
                })
                assert result.passed is True
