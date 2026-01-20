"""Model Context Protocol (MCP) Client Implementation.

Provides standardized client interface for agents to discover and invoke tools
through the MCP server following Microsoft's MCP architecture.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from mcp_server import MCPServer, ToolResult, ToolStatus, get_mcp_server


@dataclass
class ToolInfo:
    """Information about a discovered tool."""

    name: str
    description: str
    version: str
    schema: Dict[str, Any]
    tags: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolInfo":
        """Create ToolInfo from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            schema=data.get("schema", {}),
            tags=data.get("tags", []),
        )


class MCPClient:
    """MCP Client for tool discovery and invocation.

    Provides standardized interface for agents to interact with MCP server.
    Handles tool discovery, validation, and secure invocation.
    """

    def __init__(self, server: Optional[MCPServer] = None):
        """Initialize MCP client.

        Parameters
        ----------
        server : Optional[MCPServer]
            MCP server instance. If None, uses singleton.
        """
        self._server = server or get_mcp_server()
        self._local_tools: Dict[str, Any] = {}  # For local tool overrides
        self._call_history: List[ToolResult] = []

    def register_local_tool(
        self,
        name: str,
        tool_function: callable,
        description: str = "",
        schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Register a local tool override.

        Parameters
        ----------
        name : str
            Tool name
        tool_function : callable
            Local tool function
        description : str
            Tool description
        schema : Optional[Dict[str, Any]]
            Tool parameter schema
        """
        self._local_tools[name] = {
            "function": tool_function,
            "description": description,
            "schema": schema or {},
            "tags": tags or [],
        }

    def discover_tools(self, tags: Optional[List[str]] = None) -> List[ToolInfo]:
        """Discover available tools from MCP server.

        Parameters
        ----------
        tags : Optional[List[str]]
            Filter tools by tags

        Returns
        -------
        List[ToolInfo]
            List of discovered tools
        """
        try:
            tools_data = self._server.list_tools(tags)
            tools = [ToolInfo.from_dict(data) for data in tools_data]

            # Add local tool overrides
            for name, local_tool in self._local_tools.items():
                tools.append(
                    ToolInfo(
                        name=name,
                        description=local_tool["description"],
                        version="local",
                        schema=local_tool["schema"],
                        tags=local_tool.get("tags", ["local"]),
                    )
                )

            return tools

        except Exception as e:
            print(f"MCP discovery error: {e}")
            return []

    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool.

        Parameters
        ----------
        name : str
            Tool name

        Returns
        -------
        Optional[ToolInfo]
            Tool information or None if not found
        """
        try:
            if name in self._local_tools:
                local_tool = self._local_tools[name]
                return ToolInfo(
                    name=name,
                    description=local_tool["description"],
                    version="local",
                    schema=local_tool["schema"],
                    tags=local_tool.get("tags", ["local"]),
                )

            metadata = self._server.get_tool_metadata(name)
            if metadata:
                return ToolInfo.from_dict(metadata)

        except Exception as e:
            print(f"MCP tool info error: {e}")

        return None

    async def invoke_tool(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
        validate_args: bool = True,
    ) -> ToolResult:
        """Invoke a tool through MCP.

        Parameters
        ----------
        name : str
            Tool name to invoke
        args : Optional[Dict[str, Any]]
            Arguments to pass to the tool
        validate_args : bool
            Whether to validate arguments before invocation

        Returns
        -------
        ToolResult
            Tool execution result
        """
        start_time = asyncio.get_event_loop().time()
        args = args or {}

        try:
            # Check if it's a local tool override
            if name in self._local_tools:
                return await self._invoke_local_tool(name, args, start_time)

            # Use MCP server
            if validate_args:
                self._validate_args_against_schema(name, args)

            result = await self._server.call_tool(name, args)

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            result = ToolResult(
                tool_name=name,
                status=ToolStatus.ERROR,
                error_message=str(e),
                execution_time=execution_time,
            )

        # Store in local history
        self._call_history.append(result)

        return result

    async def _invoke_local_tool(
        self, name: str, args: Dict[str, Any], start_time: float
    ) -> ToolResult:
        """Invoke a local tool override.

        Parameters
        ----------
        name : str
            Tool name
        args : Dict[str, Any]
            Tool arguments
        start_time : float
            Start time for execution tracking

        Returns
        -------
        ToolResult
            Tool execution result
        """
        try:
            tool_func = self._local_tools[name]["function"]

            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**args)
            else:
                # Run sync function in thread pool
                import concurrent.futures

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(
                        executor, lambda: tool_func(**args)
                    )

            execution_time = asyncio.get_event_loop().time() - start_time

            return ToolResult(
                tool_name=name,
                status=ToolStatus.SUCCESS,
                result=result,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return ToolResult(
                tool_name=name,
                status=ToolStatus.ERROR,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _validate_args_against_schema(
        self, tool_name: str, args: Dict[str, Any]
    ) -> None:
        """Validate arguments against tool schema.

        Parameters
        ----------
        tool_name : str
            Name of the tool
        args : Dict[str, Any]
            Arguments to validate

        Raises
        ------
        ValueError
            If validation fails
        """
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found")

        schema = tool_info.schema
        if not schema:
            return  # No schema to validate against

        # Basic validation
        required = schema.get("required", [])
        for field in required:
            if field not in args:
                raise ValueError(f"Missing required argument: {field}")

        # Type checking
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

        return True

    def get_call_history(
        self, tool_name: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get call history for this client.

        Parameters
        ----------
        tool_name : Optional[str]
            Filter by tool name
        limit : int
            Maximum number of records

        Returns
        -------
        List[Dict[str, Any]]
            List of call history records
        """
        from dataclasses import asdict

        history = self._call_history

        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]

        return [asdict(r) for r in history[-limit:]]

    def get_server_stats(self) -> Dict[str, Any]:
        """Get MCP server statistics.

        Returns
        -------
        Dict[str, Any]
            Server statistics
        """
        try:
            return self._server.get_stats()
        except Exception as e:
            return {"error": str(e)}

    def find_tools_by_capability(self, capability: str) -> List[ToolInfo]:
        """Find tools by capability (searches in description and tags).

        Parameters
        ----------
        capability : str
            Capability to search for

        Returns
        -------
        List[ToolInfo]
            Tools that match the capability
        """
        all_tools = self.discover_tools()
        matching_tools = []

        search_term = capability.lower()

        for tool in all_tools:
            if search_term in tool.description.lower() or any(
                search_term in tag.lower() for tag in tool.tags
            ):
                matching_tools.append(tool)

        return matching_tools


# Singleton instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client(server: Optional[MCPServer] = None) -> MCPClient:
    """Get or create MCP client singleton instance.

    Parameters
    ----------
    server : Optional[MCPServer]
        MCP server instance

    Returns
    -------
    MCPClient
        The MCP client instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(server)
    return _mcp_client


if __name__ == "__main__":
    # Example usage
    client = get_mcp_client()

    print("MCP Client initialized")
    print(f"Available tools: {len(client.discover_tools())}")

    # Example tool invocation (would need server running)
    async def test_call():
        try:
            result = await client.invoke_tool(
                "calculator", {"a": 10, "b": 5, "operation": "add"}
            )
            print(f"Tool call result: {result}")
        except Exception as e:
            print(f"Tool call error: {e}")

    # Uncomment to test (requires MCP server)
    # asyncio.run(test_call())
