"""
Tool Registry Service.

Manages available tools, their definitions, and handlers.
"""

from __future__ import annotations

from typing import Any

from src.domain.entities.tool import Tool
from src.infrastructure.tools.executor import ToolExecutor
from src.infrastructure.tools.handlers.file_handler import FileReadHandler, FileWriteHandler
from src.infrastructure.tools.sandbox import Sandbox


class ToolRegistry:
    """Registry for tools and their handlers."""

    def __init__(self, sandbox: Sandbox | None = None) -> None:
        """Initialize registry with executor and default handlers."""
        self.executor = ToolExecutor(sandbox)
        self.tools: dict[str, Tool] = {}
        
        # Register default handlers
        self.executor.register_handler("file_read", FileReadHandler(self.executor.sandbox))
        self.executor.register_handler("file_write", FileWriteHandler(self.executor.sandbox))
        self.executor.register_handler("save_file", FileWriteHandler(self.executor.sandbox))  # Alias

    def register_tool(self, tool: Tool) -> None:
        """Register a tool definition."""
        self.tools[tool.id] = tool

    def get_tool(self, tool_id: str) -> Tool | None:
        """Get tool definition by ID."""
        return self.tools.get(tool_id)

    def get_tools_for_agent(self, agent_tool_ids: list[str]) -> list[Tool]:
        """Get tool definitions for a list of tool IDs."""
        return [
            self.tools[tid] for tid in agent_tool_ids 
            if tid in self.tools
        ]

    def execute(self, tool_id: str, params: dict[str, Any]) -> Any:
        """Execute a tool via executor."""
        return self.executor.execute(tool_id, params)
