"""
Gating utilities for skill prerequisites.

Validates that skill requirements are met before loading.
"""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass
from typing import Any


@dataclass
class GatingResult:
    """Result of gating check."""
    
    passed: bool
    reason: str = ""
    
    @staticmethod
    def ok() -> GatingResult:
        """Return successful result."""
        return GatingResult(passed=True)
    
    @staticmethod
    def fail(reason: str) -> GatingResult:
        """Return failed result with reason."""
        return GatingResult(passed=False, reason=reason)


def check_skill_requirements(metadata: dict[str, Any]) -> GatingResult:
    """
    Check if all skill requirements are satisfied.
    
    Args:
        metadata: Skill metadata dict containing 'requires' and 'os' keys.
        
    Returns:
        GatingResult indicating pass/fail.
    """
    requires = metadata.get("requires", {})
    
    # Check required binaries
    bins = requires.get("bins", [])
    for binary in bins:
        if not binary_exists(binary):
            return GatingResult.fail(f"Missing required binary: {binary}")
    
    # Check 'anyBins' - at least one must exist
    any_bins = requires.get("anyBins", [])
    if any_bins:
        if not any(binary_exists(b) for b in any_bins):
            return GatingResult.fail(
                f"None of the required binaries found: {', '.join(any_bins)}"
            )
    
    # Check required environment variables
    env_vars = requires.get("env", [])
    for env_var in env_vars:
        if not os.getenv(env_var):
            return GatingResult.fail(f"Missing required env var: {env_var}")
    
    # Check OS compatibility
    allowed_os = metadata.get("os", [])
    if allowed_os:
        current_os = get_current_os()
        if current_os not in allowed_os:
            return GatingResult.fail(
                f"OS not supported: {current_os}. Allowed: {', '.join(allowed_os)}"
            )
    
    return GatingResult.ok()


def binary_exists(binary: str) -> bool:
    """
    Check if a binary exists in PATH.
    
    Args:
        binary: Binary name to check.
        
    Returns:
        True if binary is found.
    """
    return shutil.which(binary) is not None


def get_current_os() -> str:
    """
    Get current OS identifier.
    
    Returns:
        OS identifier: 'darwin' (macOS), 'linux', 'win32' (Windows)
    """
    system = platform.system().lower()
    os_map = {
        "darwin": "darwin",
        "linux": "linux",
        "windows": "win32",
    }
    return os_map.get(system, system)


def check_binary_requirement(binaries: list[str]) -> GatingResult:
    """
    Check if all required binaries exist.
    
    Args:
        binaries: List of binary names.
        
    Returns:
        GatingResult.
    """
    for binary in binaries:
        if not binary_exists(binary):
            return GatingResult.fail(f"Missing binary: {binary}")
    return GatingResult.ok()


def check_any_binary_requirement(binaries: list[str]) -> GatingResult:
    """
    Check if at least one binary exists.
    
    Args:
        binaries: List of binary names.
        
    Returns:
        GatingResult.
    """
    if not binaries:
        return GatingResult.ok()
    
    if any(binary_exists(b) for b in binaries):
        return GatingResult.ok()
    
    return GatingResult.fail(f"None of binaries found: {', '.join(binaries)}")


def check_env_requirement(env_vars: list[str]) -> GatingResult:
    """
    Check if all required environment variables are set.
    
    Args:
        env_vars: List of env var names.
        
    Returns:
        GatingResult.
    """
    for env_var in env_vars:
        if not os.getenv(env_var):
            return GatingResult.fail(f"Missing env var: {env_var}")
    return GatingResult.ok()


def check_os_requirement(allowed_os: list[str]) -> GatingResult:
    """
    Check if current OS is in allowed list.
    
    Args:
        allowed_os: List of allowed OS identifiers.
        
    Returns:
        GatingResult.
    """
    if not allowed_os:
        return GatingResult.ok()
    
    current = get_current_os()
    if current in allowed_os:
        return GatingResult.ok()
    
    return GatingResult.fail(f"OS {current} not in allowed: {', '.join(allowed_os)}")
