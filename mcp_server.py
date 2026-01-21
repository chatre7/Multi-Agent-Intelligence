"""Model Context Protocol (MCP) Server Implementation.

Provides standardized tool interface for multi-agent system following Microsoft's MCP architecture.
Exposes tools as standardized service that agents can discover and invoke.
"""

import asyncio
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ToolStatus(Enum):
    """Tool execution status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""

    name: str
    description: str
    version: str = "1.0.0"
    schema: Dict[str, Any] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    tags: List[str] = None

    def __post_init__(self):
        if self.schema is None:
            self.schema = {}
        if self.tags is None:
            self.tags = []


@dataclass
class ToolResult:
    """Result of tool execution."""

    tool_name: str
    status: ToolStatus
    result: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class MCPServer:
    """MCP Server for tool registration and invocation.

    Provides standardized interface for tools following MCP specification.
    Supports tool discovery, registration, and secure invocation.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._tool_functions: Dict[str, Callable] = {}
        self._execution_history: List[ToolResult] = []
        self._max_history_size = 1000

    def register_tool(
        self,
        name: str,
        tool_function: Callable,
        description: str,
        schema: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Register a tool with the MCP server.

        Parameters
        ----------
        name : str
            Unique name for the tool
        tool_function : Callable
            Function to execute for the tool
        description : str
            Human-readable description
        schema : Optional[Dict[str, Any]]
            JSON schema for tool parameters
        version : str
            Tool version
        timeout_seconds : float
            Maximum execution time
        max_retries : int
            Maximum retry attempts
        tags : Optional[List[str]]
            Tags for tool categorization

        Returns
        -------
        bool
            True if registration successful
        """
        if name in self._tools:
            print(f"Warning: Tool '{name}' already registered, overwriting")

        metadata = ToolMetadata(
            name=name,
            description=description,
            version=version,
            schema=schema or {},
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            tags=tags or [],
        )

        self._tools[name] = metadata
        self._tool_functions[name] = tool_function

        print(f"✓ Tool '{name}' registered with MCP Server")
        return True

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool from the MCP server.

        Parameters
        ----------
        name : str
            Name of the tool to unregister

        Returns
        -------
        bool
            True if unregistration successful
        """
        if name in self._tools:
            del self._tools[name]
            del self._tool_functions[name]
            print(f"✓ Tool '{name}' unregistered from MCP Server")
            return True

        return False

    def list_tools(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List all available tools, optionally filtered by tags.

        Parameters
        ----------
        tags : Optional[List[str]]
            Filter tools by these tags

        Returns
        -------
        List[Dict[str, Any]]
            List of tool metadata dictionaries
        """
        tools = []

        for metadata in self._tools.values():
            if tags is None or any(tag in metadata.tags for tag in tags):
                tools.append(asdict(metadata))

        return tools

    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool.

        Parameters
        ----------
        name : str
            Name of the tool

        Returns
        -------
        Optional[Dict[str, Any]]
            Tool metadata or None if not found
        """
        if name in self._tools:
            return asdict(self._tools[name])
        return None

    async def call_tool(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
        timeout_override: Optional[float] = None,
    ) -> ToolResult:
        """Call a tool using the MCP protocol.

        Parameters
        ----------
        name : str
            Name of the tool to call
        args : Optional[Dict[str, Any]]
            Arguments to pass to the tool
        timeout_override : Optional[float]
            Override default timeout

        Returns
        -------
        ToolResult
            Result of the tool execution
        """
        start_time = asyncio.get_event_loop().time()

        if name not in self._tools:
            result = ToolResult(
                tool_name=name,
                status=ToolStatus.ERROR,
                error_message=f"Tool '{name}' not found",
                execution_time=asyncio.get_event_loop().time() - start_time,
            )
            self._add_to_history(result)
            return result

        metadata = self._tools[name]
        tool_func = self._tool_functions[name]

        timeout = timeout_override or metadata.timeout_seconds
        args = args or {}

        try:
            # Validate arguments against schema if provided
            if metadata.schema:
                self._validate_args(args, metadata.schema)

            # Execute tool with timeout
            result = await asyncio.wait_for(
                self._execute_tool(tool_func, args), timeout=timeout
            )

            execution_time = asyncio.get_event_loop().time() - start_time

            tool_result = ToolResult(
                tool_name=name,
                status=ToolStatus.SUCCESS,
                result=result,
                execution_time=execution_time,
            )

        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - start_time
            tool_result = ToolResult(
                tool_name=name,
                status=ToolStatus.TIMEOUT,
                error_message=f"Tool execution timed out after {timeout}s",
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            tool_result = ToolResult(
                tool_name=name,
                status=ToolStatus.ERROR,
                error_message=str(e),
                execution_time=execution_time,
            )

        self._add_to_history(tool_result)
        return tool_result

    def _validate_args(self, args: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Basic argument validation against schema.

        Parameters
        ----------
        args : Dict[str, Any]
            Arguments to validate
        schema : Dict[str, Any]
            JSON schema for validation

        Raises
        ------
        ValueError
            If validation fails
        """
        # Basic validation - check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in args:
                raise ValueError(f"Missing required argument: {field}")

        # Type checking (basic)
        properties = schema.get("properties", {})
        for arg_name, arg_value in args.items():
            if arg_name in properties:
                expected_type = properties[arg_name].get("type")
                if expected_type and not self._check_type(arg_value, expected_type):
                    raise ValueError(
                        f"Argument '{arg_name}' must be of type {expected_type}"
                    )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type.

        Parameters
        ----------
        value : Any
            Value to check
        expected_type : str
            Expected type string

        Returns
        -------
        bool
            True if type matches
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Allow unknown types

    async def _execute_tool(self, tool_func: Callable, args: Dict[str, Any]) -> Any:
        """Execute a tool function.

        Parameters
        ----------
        tool_func : Callable
            Tool function to execute
        args : Dict[str, Any]
            Arguments to pass

        Returns
        -------
        Any
            Tool execution result
        """
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**args)
        else:
            # Run sync function in thread pool
            import concurrent.futures

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, lambda: tool_func(**args))

    def _add_to_history(self, result: ToolResult) -> None:
        """Add result to execution history.

        Parameters
        ----------
        result : ToolResult
            Tool execution result
        """
        self._execution_history.append(result)

        # Keep history size manageable
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size :]

    def get_execution_history(
        self, tool_name: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history, optionally filtered by tool.

        Parameters
        ----------
        tool_name : Optional[str]
            Filter by specific tool name
        limit : int
            Maximum number of records to return

        Returns
        -------
        List[Dict[str, Any]]
            List of execution results
        """
        history = self._execution_history

        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]

        return [asdict(r) for r in history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get MCP server statistics.

        Returns
        -------
        Dict[str, Any]
            Server statistics
        """
        total_calls = len(self._execution_history)
        successful_calls = sum(
            1 for r in self._execution_history if r.status == ToolStatus.SUCCESS
        )
        error_calls = sum(
            1 for r in self._execution_history if r.status == ToolStatus.ERROR
        )
        timeout_calls = sum(
            1 for r in self._execution_history if r.status == ToolStatus.TIMEOUT
        )

        return {
            "total_tools": len(self._tools),
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "error_calls": error_calls,
            "timeout_calls": timeout_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0.0,
            "tools": list(self._tools.keys()),
        }


# Singleton instance
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get or create MCP server singleton instance.

    Returns
    -------
    MCPServer
        The MCP server instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


if __name__ == "__main__":
    # Example usage
    server = get_mcp_server()

    # Register example tools
    async def calculator(a: float, b: float, operation: str) -> float:
        """Simple calculator tool."""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

    server.register_tool(
        name="calculator",
        tool_function=calculator,
        description="Perform basic arithmetic operations",
        schema={
            "type": "object",
            "required": ["a", "b", "operation"],
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Arithmetic operation",
                },
            },
        },
        tags=["math", "calculator"],
    )

    print("MCP Server initialized with calculator tool")
    print(f"Available tools: {server.list_tools()}")
