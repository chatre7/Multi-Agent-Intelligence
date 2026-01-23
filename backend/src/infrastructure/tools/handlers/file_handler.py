"""
File Tool Handlers.

Handlers for file_read and file_write tools using the Sandbox.
"""

from __future__ import annotations

from typing import Any

from src.infrastructure.tools.sandbox import Sandbox


class FileReadHandler:
    """Handler for file_read tool."""

    def __init__(self, sandbox: Sandbox) -> None:
        self.sandbox = sandbox

    def __call__(self, params: dict[str, Any]) -> str:
        """
        Execute file_read.
        
        Args:
            params: Must contain 'file_path'.
            
        Returns:
            File content.
        """
        file_path = params.get("file_path")
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
            
        return self.sandbox.read_file(file_path)


class FileWriteHandler:
    """Handler for file_write tool."""

    def __init__(self, sandbox: Sandbox) -> None:
        self.sandbox = sandbox

    def __call__(self, params: dict[str, Any]) -> str:
        """
        Execute file_write.
        
        Args:
            params: Must contain 'file_path' and 'content'.
            
        Returns:
            Success message.
        """
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        if content is None:
            raise ValueError("Missing required parameter: content")
            
        written_path = self.sandbox.write_file(file_path, content)
        return f"Successfully wrote to {params['file_path']} (saved at {written_path})"
