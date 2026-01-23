"""
Tool Executor Service.

Handles secure execution of tools using handlers and sandbox.
"""

from __future__ import annotations

from typing import Any, Callable

from .sandbox import Sandbox


class ToolExecutor:
    """
    Executes tools via registered handlers.
    Integration point for Sandbox and tool execution logic.
    """

    def __init__(self, sandbox: Sandbox | None = None) -> None:
        """
        Initialize tool executor.
        
        Args:
            sandbox: Sandbox instance for safe file operations.
                     Constructs default Sandbox if None.
        """
        self.sandbox = sandbox or Sandbox()
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_handler(self, tool_id: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        """
        Register a handler for a tool.
        
        Args:
            tool_id: Tool identifier.
            handler: Callable taking params dict and returning result.
        """
        self._handlers[tool_id] = handler

    def execute(self, tool_id: str, params: dict[str, Any]) -> Any:
        """
        Execute a tool by ID.
        
        Args:
            tool_id: Tool identifier.
            params: Parameters for the tool.
            
        Returns:
            Result of execution.
            
        Raises:
            ValueError: If tool is not registered.
            Exception: Any exception raised by the tool handler.
        """
        if tool_id not in self._handlers:
            raise ValueError(f"Unknown tool: {tool_id}")
            
        handler = self._handlers[tool_id]
        return handler(params)
