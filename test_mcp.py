"""Unit tests for MCP (Model Context Protocol) components."""

import pytest
import asyncio
from mcp_server import MCPServer, ToolStatus, get_mcp_server
from mcp_client import MCPClient, get_mcp_client


class TestMCPServer:
    """Test suite for MCP Server."""

    @pytest.fixture
    def server(self):
        """Create fresh MCP server for each test."""
        return MCPServer()

    def test_server_initialization(self, server):
        """Test MCP server initializes correctly."""
        assert server._tools == {}
        assert server._tool_functions == {}
        assert len(server._execution_history) == 0

    def test_register_tool(self, server):
        """Test tool registration."""

        def test_tool(x: int, y: int) -> int:
            return x + y

        success = server.register_tool(
            name="add",
            tool_function=test_tool,
            description="Add two numbers",
            schema={
                "type": "object",
                "required": ["x", "y"],
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
            },
            tags=["math", "arithmetic"],
        )

        assert success is True
        assert "add" in server._tools
        assert "add" in server._tool_functions
        assert server._tools["add"].description == "Add two numbers"
        assert "math" in server._tools["add"].tags

    def test_register_duplicate_tool(self, server):
        """Test registering duplicate tool."""

        def tool1():
            return "tool1"

        def tool2():
            return "tool2"

        server.register_tool("test", tool1, "Test tool")
        success = server.register_tool("test", tool2, "Updated tool")

        assert success is True
        assert server._tool_functions["test"] == tool2

    def test_unregister_tool(self, server):
        """Test tool unregistration."""

        def test_tool():
            return "test"

        server.register_tool("test", test_tool, "Test tool")
        success = server.unregister_tool("test")

        assert success is True
        assert "test" not in server._tools
        assert "test" not in server._tool_functions

    def test_unregister_nonexistent_tool(self, server):
        """Test unregistering nonexistent tool."""
        success = server.unregister_tool("nonexistent")
        assert success is False

    def test_list_tools(self, server):
        """Test listing all tools."""

        def tool1():
            return "tool1"

        def tool2():
            return "tool2"

        server.register_tool("tool1", tool1, "First tool", tags=["tag1"])
        server.register_tool("tool2", tool2, "Second tool", tags=["tag2"])

        tools = server.list_tools()
        assert len(tools) == 2
        assert any(t["name"] == "tool1" for t in tools)
        assert any(t["name"] == "tool2" for t in tools)

    def test_list_tools_with_tags(self, server):
        """Test listing tools filtered by tags."""

        def tool1():
            return "tool1"

        def tool2():
            return "tool2"

        server.register_tool("tool1", tool1, "First tool", tags=["math", "arithmetic"])
        server.register_tool("tool2", tool2, "Second tool", tags=["text", "processing"])

        math_tools = server.list_tools(tags=["math"])
        assert len(math_tools) == 1
        assert math_tools[0]["name"] == "tool1"

        text_tools = server.list_tools(tags=["text"])
        assert len(text_tools) == 1
        assert text_tools[0]["name"] == "tool2"

    def test_get_tool_metadata(self, server):
        """Test getting tool metadata."""

        def test_tool():
            return "test"

        server.register_tool("test", test_tool, "Test tool", tags=["test"])

        metadata = server.get_tool_metadata("test")
        assert metadata is not None
        assert metadata["name"] == "test"
        assert metadata["description"] == "Test tool"
        assert "test" in metadata["tags"]

    def test_get_nonexistent_tool_metadata(self, server):
        """Test getting metadata for nonexistent tool."""
        metadata = server.get_tool_metadata("nonexistent")
        assert metadata is None

    @pytest.mark.asyncio
    async def test_call_tool_success(self, server):
        """Test successful tool call."""

        def add_tool(x: int, y: int) -> int:
            return x + y

        server.register_tool(
            "add",
            add_tool,
            "Add numbers",
            schema={"type": "object", "required": ["x", "y"]},
        )

        result = await server.call_tool("add", {"x": 5, "y": 3})

        assert result.status == ToolStatus.SUCCESS
        assert result.result == 8
        assert result.tool_name == "add"
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, server):
        """Test calling nonexistent tool."""
        result = await server.call_tool("nonexistent", {})

        assert result.status == ToolStatus.ERROR
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_call_tool_validation_error(self, server):
        """Test tool call with validation error."""

        def test_tool(x: int) -> int:
            return x * 2

        server.register_tool(
            "double",
            test_tool,
            "Double number",
            schema={"type": "object", "required": ["x"]},
        )

        result = await server.call_tool("double", {})  # Missing required param

        assert result.status == ToolStatus.ERROR
        assert "missing required argument" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self, server):
        """Test tool call timeout."""

        async def slow_tool():
            await asyncio.sleep(2)
            return "done"

        server.register_tool("slow", slow_tool, "Slow tool", timeout_seconds=0.1)

        result = await server.call_tool("slow", {})

        assert result.status == ToolStatus.TIMEOUT
        assert "timed out" in result.error_message.lower()

    def test_get_execution_history(self, server):
        """Test getting execution history."""
        # Add some mock history
        from mcp_server import ToolResult
        import time

        result1 = ToolResult(
            tool_name="tool1",
            status=ToolStatus.SUCCESS,
            result="success",
            execution_time=0.1,
            timestamp=time.time(),
        )
        result2 = ToolResult(
            tool_name="tool2",
            status=ToolStatus.ERROR,
            error_message="error",
            execution_time=0.2,
            timestamp=time.time(),
        )

        server._execution_history = [result1, result2]

        history = server.get_execution_history()
        assert len(history) == 2

    def test_get_execution_history_filtered(self, server):
        """Test getting execution history for specific tool."""
        from mcp_server import ToolResult
        import time

        result1 = ToolResult(
            tool_name="tool1",
            status=ToolStatus.SUCCESS,
            execution_time=0.1,
            timestamp=time.time(),
        )
        result2 = ToolResult(
            tool_name="tool2",
            status=ToolStatus.ERROR,
            execution_time=0.2,
            timestamp=time.time(),
        )

        server._execution_history = [result1, result2]

        history = server.get_execution_history(tool_name="tool1")
        assert len(history) == 1
        assert history[0]["tool_name"] == "tool1"

    def test_get_stats(self, server):
        """Test getting server statistics."""

        def tool1():
            return "tool1"

        server.register_tool("tool1", tool1, "Tool 1")

        stats = server.get_stats()

        assert stats["total_tools"] == 1
        assert "tool1" in stats["tools"]
        assert stats["total_calls"] == 0  # No calls made yet


class TestMCPClient:
    """Test suite for MCP Client."""

    @pytest.fixture
    def client_and_server(self):
        """Create MCP client and server for testing."""
        server = MCPServer()
        client = MCPClient(server)
        return client, server

    def test_client_initialization(self, client_and_server):
        """Test MCP client initializes correctly."""
        client, server = client_and_server

        assert client._server == server
        assert client._local_tools == {}
        assert client._call_history == []

    def test_register_local_tool(self, client_and_server):
        """Test registering local tool override."""
        client, server = client_and_server

        def local_tool(x: int) -> int:
            return x * 2

        client.register_local_tool(
            name="double",
            tool_function=local_tool,
            description="Double a number",
            schema={"type": "object", "required": ["x"]},
        )

        assert "double" in client._local_tools
        assert client._local_tools["double"]["function"] == local_tool

    def test_discover_tools(self, client_and_server):
        """Test tool discovery."""
        client, server = client_and_server

        def test_tool():
            return "test"

        server.register_tool("server_tool", test_tool, "Server tool", tags=["server"])

        client.register_local_tool(
            "local_tool", test_tool, "Local tool", tags=["local"]
        )

        tools = client.discover_tools()

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "server_tool" in tool_names
        assert "local_tool" in tool_names

    def test_discover_tools_with_tags(self, client_and_server):
        """Test tool discovery with tag filtering."""
        client, server = client_and_server

        def tool1():
            return "tool1"

        def tool2():
            return "tool2"

        server.register_tool("tool1", tool1, "Tool 1", tags=["math"])
        server.register_tool("tool2", tool2, "Tool 2", tags=["text"])

        math_tools = client.discover_tools(tags=["math"])
        assert len(math_tools) == 1
        assert math_tools[0].name == "tool1"

    def test_get_tool_info_server_tool(self, client_and_server):
        """Test getting server tool information."""
        client, server = client_and_server

        def test_tool(x: int) -> int:
            return x + 1

        server.register_tool(
            "increment",
            test_tool,
            "Increment number",
            schema={"type": "object", "required": ["x"]},
        )

        tool_info = client.get_tool_info("increment")

        assert tool_info is not None
        assert tool_info.name == "increment"
        assert tool_info.description == "Increment number"
        assert "x" in tool_info.schema.get("required", [])

    def test_get_tool_info_local_tool(self, client_and_server):
        """Test getting local tool information."""
        client, server = client_and_server

        def local_tool():
            return "local"

        client.register_local_tool("local", local_tool, "Local tool")

        tool_info = client.get_tool_info("local")

        assert tool_info is not None
        assert tool_info.name == "local"
        assert tool_info.version == "local"
        assert tool_info.description == "Local tool"

    def test_get_tool_info_nonexistent(self, client_and_server):
        """Test getting information for nonexistent tool."""
        client, server = client_and_server

        tool_info = client.get_tool_info("nonexistent")
        assert tool_info is None

    @pytest.mark.asyncio
    async def test_invoke_tool_server_tool(self, client_and_server):
        """Test invoking server tool."""
        client, server = client_and_server

        def multiply(x: int, y: int) -> int:
            return x * y

        server.register_tool(
            "multiply",
            multiply,
            "Multiply numbers",
            schema={"type": "object", "required": ["x", "y"]},
        )

        result = await client.invoke_tool("multiply", {"x": 4, "y": 5})

        assert result.status.name == "SUCCESS"
        assert result.result == 20
        assert result.tool_name == "multiply"

    @pytest.mark.asyncio
    async def test_invoke_tool_local_tool(self, client_and_server):
        """Test invoking local tool."""
        client, server = client_and_server

        def local_func(text: str) -> str:
            return f"processed: {text}"

        client.register_local_tool(
            "process_text",
            local_func,
            "Process text",
            schema={"type": "object", "required": ["text"]},
        )

        result = await client.invoke_tool("process_text", {"text": "hello"})

        assert result.status.name == "SUCCESS"
        assert result.result == "processed: hello"

    @pytest.mark.asyncio
    async def test_invoke_tool_validation_error(self, client_and_server):
        """Test tool invocation with validation error."""
        client, server = client_and_server

        def test_tool(x: int) -> int:
            return x

        server.register_tool(
            "test", test_tool, "Test tool", schema={"type": "object", "required": ["x"]}
        )

        result = await client.invoke_tool("test", {})  # Missing required param

        assert result.status.name == "ERROR"
        assert "missing required argument" in result.error_message.lower()

    def test_get_call_history(self, client_and_server):
        """Test getting client call history."""
        client, server = client_and_server

        # Mock some history
        from mcp_server import ToolResult
        import time

        result = ToolResult(
            tool_name="test_tool",
            status=ToolStatus.SUCCESS,
            result="success",
            execution_time=0.1,
            timestamp=time.time(),
        )

        client._call_history = [result]

        history = client.get_call_history()
        assert len(history) == 1
        assert history[0]["tool_name"] == "test_tool"

    def test_find_tools_by_capability(self, client_and_server):
        """Test finding tools by capability."""
        client, server = client_and_server

        def calc_tool():
            return "calculator"

        def text_tool():
            return "text processor"

        server.register_tool(
            "calc", calc_tool, "Calculator tool for math", tags=["math"]
        )
        server.register_tool("text", text_tool, "Text processing tool", tags=["text"])

        math_tools = client.find_tools_by_capability("math")
        assert len(math_tools) == 1
        assert math_tools[0].name == "calc"

        calc_tools = client.find_tools_by_capability("calculator")
        assert len(calc_tools) == 1
        assert calc_tools[0].name == "calc"


class TestMCPIntegration:
    """Test MCP server-client integration."""

    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self):
        """Test complete MCP workflow from registration to invocation."""
        server = MCPServer()
        client = MCPClient(server)

        # Register tool
        def greet(name: str, style: str = "formal") -> str:
            if style == "casual":
                return f"Hey {name}!"
            else:
                return f"Hello, {name}."

        server.register_tool(
            name="greet",
            tool_function=greet,
            description="Generate greeting message",
            schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Person's name"},
                    "style": {
                        "type": "string",
                        "enum": ["formal", "casual"],
                        "default": "formal",
                    },
                },
            },
            tags=["communication", "text"],
        )

        # Discover tools
        tools = client.discover_tools()
        assert len(tools) == 1
        assert tools[0].name == "greet"

        # Get tool info
        tool_info = client.get_tool_info("greet")
        assert tool_info is not None
        assert tool_info.description == "Generate greeting message"

        # Invoke tool
        result = await client.invoke_tool("greet", {"name": "Alice"})
        assert result.status.name == "SUCCESS"
        assert result.result == "Hello, Alice."

        result_casual = await client.invoke_tool(
            "greet", {"name": "Bob", "style": "casual"}
        )
        assert result_casual.status.name == "SUCCESS"
        assert result_casual.result == "Hey Bob!"

        # Check history
        server_history = server.get_execution_history()
        client_history = client.get_call_history()

        assert len(server_history) == 2
        assert len(client_history) == 2

        # Check server stats
        stats = server.get_stats()
        assert stats["total_tools"] == 1
        assert stats["total_calls"] == 2
        assert stats["successful_calls"] == 2
        assert stats["success_rate"] == 1.0


class TestMCPSingleton:
    """Test MCP singleton patterns."""

    def test_server_singleton(self):
        """Test MCP server singleton."""
        server1 = get_mcp_server()
        server2 = get_mcp_server()

        assert server1 is server2

    def test_client_singleton(self):
        """Test MCP client singleton."""
        client1 = get_mcp_client()
        client2 = get_mcp_client()

        assert client1 is client2
