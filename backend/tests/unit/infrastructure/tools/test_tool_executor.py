import pytest
from unittest.mock import Mock, patch
from src.infrastructure.tools.executor import ToolExecutor
from src.infrastructure.tools.handlers.file_handler import FileReadHandler, FileWriteHandler
from src.infrastructure.tools.sandbox import Sandbox, SecurityError
from src.domain.entities.tool import Tool

@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    return Sandbox(root_dir=str(root))

@pytest.fixture
def executor(sandbox):
    return ToolExecutor(sandbox=sandbox)

def test_executor_registers_handler(executor):
    """Test registering a tool handler."""
    mock_handler = Mock(return_value="success")
    executor.register_handler("test_tool", mock_handler)
    
    result = executor.execute("test_tool", {})
    assert result == "success"
    mock_handler.assert_called_once_with({})

def test_executor_unknown_tool_raises_error(executor):
    """Test executing unknown tool raises error."""
    with pytest.raises(ValueError) as exc:
        executor.execute("unknown_tool", {})
    assert "Unknown tool" in str(exc.value)

def test_file_write_handler_uses_sandbox(sandbox):
    """Test file write handler uses sandbox correctly."""
    handler = FileWriteHandler(sandbox)
    params = {"file_path": "test.txt", "content": "hello"}
    
    result = handler(params)
    
    # Check return value
    assert "Successfully wrote" in result
    assert "test.txt" in result
    
    # Check actual file
    assert sandbox.read_file("test.txt") == "hello"

def test_file_write_handler_security_error(sandbox):
    """Test file write handler catches security errors."""
    handler = FileWriteHandler(sandbox)
    params = {"file_path": "../hack.txt", "content": "exploit"}
    
    with pytest.raises(SecurityError):
        handler(params)

def test_file_read_handler_uses_sandbox(sandbox):
    """Test file read handler uses sandbox correctly."""
    sandbox.write_file("data.json", '{"key": "value"}')
    
    handler = FileReadHandler(sandbox)
    result = handler({"file_path": "data.json"})
    
    assert '{"key": "value"}' in result

def test_end_to_end_execution(executor, sandbox):
    """Test full execution flow through executor."""
    # Register handlers
    executor.register_handler("file_write", FileWriteHandler(sandbox))
    executor.register_handler("file_read", FileReadHandler(sandbox))
    
    # Write
    result_write = executor.execute("file_write", {"file_path": "e2e.txt", "content": "E2E Test"})
    assert "Successfully wrote" in result_write
    
    # Read
    result_read = executor.execute("file_read", {"file_path": "e2e.txt"})
    assert "E2E Test" in result_read
