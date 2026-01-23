import pytest
import os
from pathlib import Path
from src.infrastructure.tools.sandbox import Sandbox, SecurityError

@pytest.fixture
def sandbox_root(tmp_path):
    """Create a temporary directory for sandbox root."""
    root = tmp_path / "sandbox_data"
    root.mkdir()
    return root

@pytest.fixture
def sandbox(sandbox_root):
    """Initialize sandbox with temporary root."""
    return Sandbox(root_dir=str(sandbox_root))

def test_is_safe_path_inside_root(sandbox, sandbox_root):
    """Test that paths inside root are considered safe."""
    safe_path = sandbox_root / "test.txt"
    assert sandbox.is_safe_path(str(safe_path)) is True

def test_is_safe_path_outside_root_fails(sandbox, sandbox_root):
    """Test that paths outside root are unsafe."""
    unsafe_path = sandbox_root.parent / "system.txt"
    assert sandbox.is_safe_path(str(unsafe_path)) is False

def test_path_traversal_attack_fails(sandbox, sandbox_root):
    """Test protection against path traversal attacks."""
    # Attempt to go up to parent directory
    unsafe_path = str(sandbox_root) + "/../passwd"
    assert sandbox.is_safe_path(unsafe_path) is False

def test_write_file_success(sandbox, sandbox_root):
    """Test writing file to safe location."""
    file_path = "data.txt"
    content = "Hello Sandbox"
    
    result_path = sandbox.write_file(file_path, content)
    
    # Verify file exists and content matches
    full_path = sandbox_root / file_path
    assert full_path.exists()
    assert full_path.read_text() == content
    assert str(result_path) == str(full_path)

def test_write_file_security_error(sandbox):
    """Test attempting to write outside sandbox raises error."""
    with pytest.raises(SecurityError) as exc:
        sandbox.write_file("../secrets.txt", "exploit")
    
    assert "Access denied" in str(exc.value)

def test_read_file_success(sandbox, sandbox_root):
    """Test reading existing file."""
    file_path = "read_me.txt"
    content = "Secret Data"
    (sandbox_root / file_path).write_text(content)
    
    read_content = sandbox.read_file(file_path)
    assert read_content == content

def test_read_file_security_error(sandbox):
    """Test attempting to read outside sandbox raises error."""
    with pytest.raises(SecurityError):
        sandbox.read_file("../../../etc/passwd")

def test_list_files(sandbox, sandbox_root):
    """Test listing files in directory."""
    (sandbox_root / "a.txt").touch()
    (sandbox_root / "b.txt").touch()
    
    files = sandbox.list_files(".")
    assert len(files) == 2
    assert "a.txt" in files
    assert "b.txt" in files
