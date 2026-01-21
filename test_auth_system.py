"""Unit tests for Authentication and RBAC System."""

import pytest
from auth_system import (
    AuthManager,
    RBACManager,
    User,
    UserRole,
    AuthError,
    PermissionError,
    get_auth_manager,
    get_rbac_manager,
)


class TestUser:
    """Test suite for User dataclass."""

    def test_user_creation(self):
        """Test User creation with defaults."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
        )

        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.failed_login_attempts == 0

    def test_user_to_dict(self):
        """Test User to_dict conversion."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
        )

        data = user.to_dict()
        assert data["id"] == "user123"
        assert data["role"] == "user"  # Enum converted to string
        assert data["is_active"] is True

    def test_user_from_dict(self):
        """Test User from_dict creation."""
        data = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "user",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
        }

        user = User.from_dict(data)
        assert user.id == "user123"
        assert user.role == UserRole.USER
        assert user.is_active is True


class TestRBACManager:
    """Test suite for RBACManager."""

    @pytest.fixture
    def rbac_manager(self):
        """Create fresh RBAC manager."""
        return RBACManager()

    def test_get_role_permissions_admin(self, rbac_manager):
        """Test getting admin role permissions."""
        permissions = rbac_manager.get_role_permissions(UserRole.ADMIN)
        assert "agent:create" in permissions
        assert "user:manage" in permissions
        assert len(permissions) > 10  # Should have many permissions

    def test_get_role_permissions_user(self, rbac_manager):
        """Test getting user role permissions."""
        permissions = rbac_manager.get_role_permissions(UserRole.USER)
        assert "agent:read" in permissions
        assert "tool:execute" in permissions
        assert "user:manage" not in permissions  # Users shouldn't have user management

    def test_get_user_permissions_with_role(self, rbac_manager):
        """Test getting user permissions based on role."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.DEVELOPER,
        )

        permissions = rbac_manager.get_user_permissions(user)
        assert "agent:create" in permissions
        assert "tool:register" in permissions
        assert "user:manage" not in permissions

    def test_add_custom_permission(self, rbac_manager):
        """Test adding custom permission to user."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
        )

        rbac_manager.add_custom_permission("user123", "custom:permission")
        permissions = rbac_manager.get_user_permissions(user)

        assert "custom:permission" in permissions

    def test_check_permission_success(self, rbac_manager):
        """Test permission checking success."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
        )

        assert rbac_manager.check_permission(user, "agent:read") is True
        assert rbac_manager.check_permission(user, "user:manage") is False

    def test_require_permission_success(self, rbac_manager):
        """Test requiring permission success."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.ADMIN,
        )

        # Should not raise
        rbac_manager.require_permission(user, "user:manage")

    def test_require_permission_failure(self, rbac_manager):
        """Test requiring permission failure."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
        )

        with pytest.raises(PermissionError):
            rbac_manager.require_permission(user, "user:manage")

    def test_get_all_roles(self, rbac_manager):
        """Test getting all roles information."""
        roles = rbac_manager.get_all_roles()

        assert len(roles) == 6  # All UserRole enum values
        role_names = [r["role"] for r in roles]
        assert "admin" in role_names
        assert "user" in role_names

        # Check admin has many permissions
        admin_role = next(r for r in roles if r["role"] == "admin")
        assert len(admin_role["permissions"]) > 10


class TestAuthManager:
    """Test suite for AuthManager."""

    @pytest.fixture
    def auth_manager(self, tmp_path):
        """Create fresh auth manager with temp storage."""
        storage_path = str(tmp_path / "test_users.json")
        # Create AuthManager instance with custom storage path
        from auth_system import AuthConfig

        config = AuthConfig()
        manager = AuthManager(config, storage_path)
        return manager

    def test_create_user(self, auth_manager):
        """Test creating a new user."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            role=UserRole.USER,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Should be hashed

    def test_create_duplicate_username_raises_error(self, auth_manager):
        """Test creating user with duplicate username."""
        auth_manager.create_user(
            "user1", "email1@test.com", "User 1", "pass", UserRole.USER
        )

        with pytest.raises(AuthError, match="Username already exists"):
            auth_manager.create_user(
                "user1", "email2@test.com", "User 2", "pass", UserRole.USER
            )

    def test_create_duplicate_email_raises_error(self, auth_manager):
        """Test creating user with duplicate email."""
        auth_manager.create_user(
            "user1", "email@test.com", "User 1", "pass", UserRole.USER
        )

        with pytest.raises(AuthError, match="Email already exists"):
            auth_manager.create_user(
                "user2", "email@test.com", "User 2", "pass", UserRole.USER
            )

    def test_authenticate_user_success(self, auth_manager):
        """Test successful user authentication."""
        auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )

        user = auth_manager.authenticate_user("user1", "password123")

        assert user.username == "user1"
        assert user.email == "email@test.com"

    def test_authenticate_user_wrong_password(self, auth_manager):
        """Test authentication with wrong password."""
        auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )

        with pytest.raises(AuthError, match="Invalid credentials"):
            auth_manager.authenticate_user("user1", "wrongpassword")

    def test_authenticate_user_wrong_username(self, auth_manager):
        """Test authentication with wrong username."""
        with pytest.raises(AuthError, match="Invalid credentials"):
            auth_manager.authenticate_user("nonexistent", "password123")

    def test_authenticate_user_account_locked(self, auth_manager):
        """Test authentication with locked account."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )

        # Simulate account lock
        user.failed_login_attempts = 6
        user.locked_until = "2099-01-01T00:00:00"  # Future date

        with pytest.raises(AuthError, match="Account is temporarily locked"):
            auth_manager.authenticate_user("user1", "password123")

    def test_generate_token(self, auth_manager):
        """Test token generation."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )
        user = auth_manager.authenticate_user("user1", "password123")

        token = auth_manager.generate_token(user)

        assert token.token is not None
        assert token.user_id == user.id
        assert token.permissions is not None
        assert len(token.permissions) > 0

    def test_validate_token_success(self, auth_manager):
        """Test successful token validation."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )
        user = auth_manager.authenticate_user("user1", "password123")
        token = auth_manager.generate_token(user)

        validated_user, permissions = auth_manager.validate_token(token.token)

        assert validated_user.id == user.id
        assert len(permissions) > 0

    def test_validate_token_expired(self, auth_manager):
        """Test expired token validation."""
        from auth_system import AuthConfig
        import time

        # Create auth manager with very short token expiry
        config = AuthConfig(jwt_expiration_hours=0.0001)  # Very short expiry
        auth_mgr = AuthManager(config)

        user = auth_mgr.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )
        user = auth_mgr.authenticate_user("user1", "password123")
        token = auth_mgr.generate_token(user)

        # Wait for token to expire
        time.sleep(0.1)

        with pytest.raises(AuthError, match="Token expired"):
            auth_mgr.validate_token(token.token)

    def test_validate_token_invalid(self, auth_manager):
        """Test invalid token validation."""
        with pytest.raises(AuthError, match="Invalid token"):
            auth_manager.validate_token("invalid.token.here")

    def test_update_user(self, auth_manager):
        """Test updating user information."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "password123", UserRole.USER
        )

        updated_user = auth_manager.update_user(
            user.id, full_name="Updated Name", is_active=False
        )

        assert updated_user.full_name == "Updated Name"
        assert updated_user.is_active is False

    def test_update_nonexistent_user_raises_error(self, auth_manager):
        """Test updating non-existent user."""
        with pytest.raises(AuthError, match="User not found"):
            auth_manager.update_user("nonexistent", full_name="Test")

    def test_list_users(self, auth_manager):
        """Test listing users."""
        auth_manager.create_user(
            "user1", "email1@test.com", "User 1", "pass", UserRole.USER
        )
        auth_manager.create_user(
            "user2", "email2@test.com", "User 2", "pass", UserRole.ADMIN
        )

        users = auth_manager.list_users()

        assert len(users) == 2
        usernames = [u["username"] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames

    def test_change_password(self, auth_manager):
        """Test password change."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "oldpass", UserRole.USER
        )

        auth_manager.change_password(user.id, "oldpass", "newpass")

        # Should be able to authenticate with new password
        authenticated = auth_manager.authenticate_user("user1", "newpass")
        assert authenticated.username == "user1"

    def test_change_password_wrong_old_password(self, auth_manager):
        """Test password change with wrong old password."""
        user = auth_manager.create_user(
            "user1", "email@test.com", "User 1", "oldpass", UserRole.USER
        )

        with pytest.raises(AuthError, match="Current password is incorrect"):
            auth_manager.change_password(user.id, "wrongpass", "newpass")


class TestAuthSingletons:
    """Test auth system singletons."""

    def test_get_auth_manager_singleton(self):
        """Test auth manager singleton."""
        manager1 = get_auth_manager()
        manager2 = get_auth_manager()

        assert manager1 is manager2

    def test_get_rbac_manager_singleton(self):
        """Test RBAC manager singleton."""
        manager1 = get_rbac_manager()
        manager2 = get_rbac_manager()

        assert manager1 is manager2
