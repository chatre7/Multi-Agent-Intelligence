"""
Sandbox Environment for Tool Execution.

Provides a secure environment for agents to execute file operations
restricted to a specific directory (Path Whitelist).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar


class SecurityError(Exception):
    """Raised when a security violation is detected."""


class Sandbox:
    """
    Path Whitelist Sandbox.
    
    Ensures all file operations are contained within the root_dir.
    Prevents path traversal attacks relative to the root_dir.
    """
    
    DEFAULT_ROOT: ClassVar[str] = "/app/data/sandbox"

    def __init__(self, root_dir: str | None = None) -> None:
        """
        Initialize the sandbox.
        
        Args:
            root_dir: Absolute path to the sandbox root. Defaults to /app/data/sandbox.
        """
        self.root = Path(root_dir or self.DEFAULT_ROOT).resolve()
        
        # Ensure root directory exists
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

    def is_safe_path(self, path: str | Path) -> bool:
        """
        Check if a path is safe (inside sandbox root).
        
        Args:
            path: Path to check.
            
        Returns:
            True if path is inside sandbox root, False otherwise.
        """
        try:
            # Resolve absolute path and normalize
            target_path = (self.root / path).resolve()
            
            # Check if target starts with root path
            # This protects against traversal like /sandbox/../etc/passwd
            # which resolves to /etc/passwd
            return str(target_path).startswith(str(self.root))
        except (ValueError, RuntimeError):
            return False

    def _resolve_safe_path(self, path: str | Path) -> Path:
        """
        Resolve path and raise SecurityError if unsafe.
        
        Args:
            path: Relative path inside sandbox.
            
        Returns:
            Resolved absolute path.
            
        Raises:
            SecurityError: If path is unsafe.
        """
        if not self.is_safe_path(path):
            raise SecurityError(
                f"Access denied: Path '{path}' resolves outside sandbox root '{self.root}'"
            )
        return (self.root / path).resolve()

    def write_file(self, path: str, content: str) -> Path:
        """
        Write content to a file inside the sandbox.
        
        Args:
            path: Relative path to file.
            content: Text content to write.
            
        Returns:
            Absolute path of the written file.
            
        Raises:
            SecurityError: If path is unsafe.
        """
        target_path = self._resolve_safe_path(path)
        
        # Ensure parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def read_file(self, path: str) -> str:
        """
        Read content from a file inside the sandbox.
        
        Args:
            path: Relative path to file.
            
        Returns:
            File content as string.
            
        Raises:
            SecurityError: If path is unsafe.
            FileNotFoundError: If file doesn't exist.
        """
        target_path = self._resolve_safe_path(path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        if not target_path.is_file():
            raise IsADirectoryError(f"Path is a directory: {path}")
            
        return target_path.read_text(encoding="utf-8")

    def list_files(self, path: str = ".") -> list[str]:
        """
        List files in a directory inside sandbox.
        
        Args:
            path: Relative path to directory.
            
        Returns:
            List of filenames.
            
        Raises:
            SecurityError: If path is unsafe.
        """
        target_path = self._resolve_safe_path(path)
        
        if not target_path.exists():
            return []
            
        return [p.name for p in target_path.iterdir()]
