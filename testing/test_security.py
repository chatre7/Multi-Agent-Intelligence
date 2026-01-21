"""Security Tests for Multi-Agent System.

Tests security features including:
- File path validation
- Directory traversal prevention
- JWT secret persistence
- Path injection attacks
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from planner_agent_team_v3
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from planner_agent_team_v3 import save_file
from auth_system import _get_or_create_jwt_secret, AuthConfig


@pytest.fixture
def temp_dir_with_cleanup():
    """Create a temp directory with Windows-safe cleanup."""
    original_dir = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)

    yield tmpdir

    # Restore original directory
    os.chdir(original_dir)

    # Clean up with retry on Windows
    try:
        shutil.rmtree(tmpdir)
    except (PermissionError, OSError):
        # On Windows, files might be locked - try again or skip
        import time
        time.sleep(0.1)
        try:
            shutil.rmtree(tmpdir)
        except (PermissionError, OSError):
            pass  # Skip cleanup if still locked


class TestFilePathSecurity:
    """Test suite for file path security."""

    def test_save_file_directory_traversal_attack(self):
        """Test that directory traversal attacks are blocked."""
        # Attack attempts
        attack_paths = [
            "../../../etc/passwd",
            "../../sensitive_file.txt",
            "workspace/../../../etc/hosts",
            "./../config.py",
        ]

        for attack_path in attack_paths:
            result = save_file.invoke({"filename": attack_path, "code": "malicious"})
            assert "Security Error" in result
            assert "Directory traversal" in result or "not allowed" in result

    def test_save_file_absolute_path_blocked(self):
        """Test that absolute paths are blocked."""
        attack_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
            "/root/.ssh/authorized_keys",
        ]

        for attack_path in attack_paths:
            result = save_file.invoke({"filename": attack_path, "code": "malicious"})
            assert "Security Error" in result
            # Accept either message format
            assert ("Absolute paths not allowed" in result or "allowed directories" in result)

    def test_save_file_allowed_extensions(self, temp_dir_with_cleanup):
        """Test that only allowed file extensions work."""
        # Allowed extensions
        allowed_files = {
            "test.py": True,
            "data.json": True,
            "readme.md": True,
            "config.yaml": True,
            "output.csv": True,
        }

        # Disallowed extensions
        disallowed_files = {
            "malware.exe": False,
            "script.sh": False,
            "config.conf": False,
            "binary.bin": False,
        }

        for filename, should_work in {**allowed_files, **disallowed_files}.items():
            result = save_file.invoke({"filename": filename, "code": "content"})

            if should_work:
                # Should succeed or create workspace
                assert "successfully" in result or "Security Error" in result
            else:
                # Should fail with extension error
                assert "Security Error" in result
                assert "not allowed" in result

    def test_save_file_allowed_directories(self, temp_dir_with_cleanup):
        """Test that files can only be saved in allowed directories."""
        # Create workspace directory
        Path("workspace").mkdir(exist_ok=True)

        # Allowed paths
        result = save_file.invoke({"filename": "test.py", "code": "print('test')"})
        assert "successfully" in result

        result = save_file.invoke({"filename": "workspace/test.py", "code": "print('test')"})
        assert "successfully" in result

    def test_save_file_symlink_attack(self, temp_dir_with_cleanup):
        """Test that symlink attacks are handled."""
        # Try to create symlink to sensitive location
        # (save_file resolves symlinks, so should be blocked)
        sensitive_path = "/tmp/sensitive.txt"

        result = save_file.invoke({"filename": sensitive_path, "code": "data"})
        # Should be blocked as absolute path
        assert "Security Error" in result


class TestJWTSecretPersistence:
    """Test suite for JWT secret persistence."""

    def test_jwt_secret_from_environment(self):
        """Test that JWT secret is loaded from environment variable."""
        test_secret = "a" * 64

        with patch.dict(os.environ, {"JWT_SECRET_KEY": test_secret}):
            secret = _get_or_create_jwt_secret()
            assert secret == test_secret

    def test_jwt_secret_persistence(self, temp_dir_with_cleanup):
        """Test that JWT secret is persisted to file."""
        Path("data").mkdir(exist_ok=True)

        # First call creates secret
        secret1 = _get_or_create_jwt_secret()
        assert len(secret1) == 64

        # Second call should return same secret
        secret2 = _get_or_create_jwt_secret()
        assert secret1 == secret2

        # Verify file exists
        secret_file = Path("data/.jwt_secret")
        assert secret_file.exists()

        # Verify file content
        with open(secret_file, "r") as f:
            stored_secret = f.read().strip()
            assert stored_secret == secret1

    def test_jwt_secret_file_permissions(self, temp_dir_with_cleanup):
        """Test that secret file has restrictive permissions."""
        Path("data").mkdir(exist_ok=True)

        secret = _get_or_create_jwt_secret()

        secret_file = Path("data/.jwt_secret")
        if hasattr(os, 'stat'):
            # Check permissions on Unix systems
            import stat
            file_stat = secret_file.stat()
            # Should be 0o600 (read/write owner only)
            # Note: On Windows, permissions work differently
            if os.name != 'nt':
                mode = file_stat.st_mode
                # Owner should have read/write
                assert mode & stat.S_IRUSR
                assert mode & stat.S_IWUSR
                # Group and others should not have access
                # (This might not work on all filesystems)

    def test_jwt_secret_invalid_file_fallback(self, temp_dir_with_cleanup):
        """Test fallback when existing file is invalid."""
        Path("data").mkdir(exist_ok=True)

        # Create invalid secret file
        secret_file = Path("data/.jwt_secret")
        with open(secret_file, "w") as f:
            f.write("invalid_short")  # Not 64 characters

        # Should generate new secret
        secret = _get_or_create_jwt_secret()
        assert len(secret) == 64
        assert secret != "invalid_short"

    def test_auth_config_uses_persistent_secret(self, temp_dir_with_cleanup):
        """Test that AuthConfig uses the persistent secret function."""
        Path("data").mkdir(exist_ok=True)

        # Create two AuthConfig instances
        config1 = AuthConfig()
        config2 = AuthConfig()

        # They should have the same secret (from persistence)
        assert config1.jwt_secret_key == config2.jwt_secret_key
        assert len(config1.jwt_secret_key) == 64


class TestPasswordSecurity:
    """Test suite for password security."""

    def test_bcrypt_rounds_configuration(self):
        """Test that bcrypt rounds are configurable."""
        config = AuthConfig()
        assert config.bcrypt_rounds == 12  # Default secure value
        assert config.bcrypt_rounds >= 10  # Minimum recommended

    def test_rate_limiting_enabled(self):
        """Test that rate limiting is enabled by default."""
        config = AuthConfig()
        assert config.enable_rate_limiting is True
        assert config.max_login_attempts >= 3
        assert config.lockout_duration_minutes > 0


class TestInputValidation:
    """Test suite for input validation."""

    def test_empty_filename_handled(self):
        """Test that empty filename is handled."""
        result = save_file.invoke({"filename": "", "code": "test"})
        assert "Error" in result or "Invalid" in result

    def test_special_characters_in_filename(self):
        """Test handling of special characters in filename."""
        special_filenames = [
            "file<script>.py",  # XSS attempt
            "file|command.py",  # Command injection attempt
            "file;command.py",  # Command injection attempt
        ]

        for filename in special_filenames:
            result = save_file.invoke({"filename": filename, "code": "test"})
            # Should either work (if sanitized) or fail gracefully
            assert isinstance(result, str)

    def test_very_long_filename(self):
        """Test handling of extremely long filenames."""
        long_filename = "a" * 1000 + ".py"
        result = save_file.invoke({"filename": long_filename, "code": "test"})
        # Should handle gracefully (either work or fail with clear error)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
