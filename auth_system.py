"""Authentication and Authorization System.

Implements RBAC (Role-Based Access Control) following Microsoft's security guidelines.
Provides JWT-based authentication, role management, and permission checking.
"""

import os
import json
import time
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import jwt as jwt_lib
import bcrypt as bcrypt_lib
from pydantic import BaseModel, Field


class UserRole(Enum):
    """User roles in the system."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    USER = "user"
    AGENT = "agent"  # For agent-to-agent communication
    GUEST = "guest"


class Permission(Enum):
    """System permissions."""

    # Agent Management
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_PROMOTE = "agent:promote"
    AGENT_DEPLOY = "agent:deploy"

    # Tool Management
    TOOL_EXECUTE = "tool:execute"
    TOOL_REGISTER = "tool:register"
    TOOL_MANAGE = "tool:manage"

    # System Monitoring
    MONITOR_READ = "monitor:read"
    MONITOR_ADMIN = "monitor:admin"

    # User Management
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"

    # MCP Access
    MCP_ACCESS = "mcp:access"
    MCP_ADMIN = "mcp:admin"

    # Health & Metrics
    HEALTH_READ = "health:read"
    METRICS_READ = "metrics:read"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: float = 24.0
    bcrypt_rounds: int = 12
    enable_rate_limiting: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


@dataclass
class User:
    """User account information."""

    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    password_hash: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["role"] = self.role.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["role"] = UserRole(data_copy["role"])
        return cls(**data_copy)


@dataclass
class AccessToken:
    """JWT access token information."""

    token: str
    user_id: str
    expires_at: str
    issued_at: str
    permissions: List[str]


class AuthError(Exception):
    """Authentication error."""

    pass


class PermissionError(Exception):
    """Permission denied error."""

    pass


class RBACManager:
    """Role-Based Access Control manager."""

    # Role permissions mapping
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            # All permissions
            p.value
            for p in Permission
        ],
        UserRole.DEVELOPER: [
            Permission.AGENT_CREATE.value,
            Permission.AGENT_READ.value,
            Permission.AGENT_UPDATE.value,
            Permission.TOOL_EXECUTE.value,
            Permission.TOOL_REGISTER.value,
            Permission.MONITOR_READ.value,
            Permission.MCP_ACCESS.value,
            Permission.HEALTH_READ.value,
            Permission.METRICS_READ.value,
        ],
        UserRole.OPERATOR: [
            Permission.AGENT_READ.value,
            Permission.AGENT_PROMOTE.value,
            Permission.AGENT_DEPLOY.value,
            Permission.TOOL_EXECUTE.value,
            Permission.MONITOR_READ.value,
            Permission.MONITOR_ADMIN.value,
            Permission.MCP_ACCESS.value,
            Permission.HEALTH_READ.value,
            Permission.METRICS_READ.value,
        ],
        UserRole.USER: [
            Permission.AGENT_READ.value,
            Permission.TOOL_EXECUTE.value,
            Permission.MONITOR_READ.value,
            Permission.MCP_ACCESS.value,
            Permission.HEALTH_READ.value,
        ],
        UserRole.AGENT: [
            Permission.AGENT_READ.value,
            Permission.TOOL_EXECUTE.value,
            Permission.MCP_ACCESS.value,
            Permission.HEALTH_READ.value,
        ],
        UserRole.GUEST: [
            Permission.AGENT_READ.value,
            Permission.HEALTH_READ.value,
        ],
    }

    def __init__(self):
        self._custom_permissions: Dict[str, List[str]] = {}

    def get_role_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for a role."""
        return self.ROLE_PERMISSIONS.get(role, [])

    def get_user_permissions(self, user: User) -> List[str]:
        """Get permissions for a user."""
        permissions = self.get_role_permissions(user.role)

        # Add custom permissions if any
        if user.id in self._custom_permissions:
            permissions.extend(self._custom_permissions[user.id])

        return list(set(permissions))  # Remove duplicates

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user)
        return permission in user_permissions

    def require_permission(self, user: User, permission: str) -> None:
        """Require a permission, raise error if not granted."""
        if not self.check_permission(user, permission):
            raise PermissionError(f"Permission denied: {permission}")

    def add_custom_permission(self, user_id: str, permission: str) -> None:
        """Add custom permission to a user."""
        if user_id not in self._custom_permissions:
            self._custom_permissions[user_id] = []
        if permission not in self._custom_permissions[user_id]:
            self._custom_permissions[user_id].append(permission)

    def remove_custom_permission(self, user_id: str, permission: str) -> None:
        """Remove custom permission from a user."""
        if user_id in self._custom_permissions:
            self._custom_permissions[user_id] = [
                p for p in self._custom_permissions[user_id] if p != permission
            ]

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles with their permissions."""
        roles = []
        for role in UserRole:
            roles.append(
                {"role": role.value, "permissions": self.get_role_permissions(role)}
            )
        return roles


class AuthManager:
    """Authentication manager with JWT tokens and user management."""

    def __init__(
        self, config: Optional[AuthConfig] = None, storage_path: str = "./users.json"
    ):
        self.config = config or AuthConfig()
        self.rbac = RBACManager()
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._users: Dict[str, User] = {}
        self._active_tokens: Dict[str, AccessToken] = {}
        self._load_users()

    def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        password: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Create a new user account."""
        if username in [u.username for u in self._users.values()]:
            raise AuthError(f"Username already exists: {username}")

        if email in [u.email for u in self._users.values()]:
            raise AuthError(f"Email already exists: {email}")

        user_id = self._generate_user_id()
        password_hash = self._hash_password(password)

        user = User(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            password_hash=password_hash,
        )

        self._users[user_id] = user
        self._save_users()
        return user

    def authenticate_user(self, username_or_email: str, password: str) -> User:
        """Authenticate a user with username/email and password."""
        user = self._find_user_by_username_or_email(username_or_email)
        if not user:
            raise AuthError("Invalid credentials")

        if not user.is_active:
            raise AuthError("Account is disabled")

        # Check if account is locked
        if self._is_account_locked(user):
            raise AuthError(
                "Account is temporarily locked due to failed login attempts"
            )

        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._record_failed_login(user)
            raise AuthError("Invalid credentials")

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow().isoformat()
        self._save_users()

        return user

    def generate_token(self, user: User) -> AccessToken:
        """Generate JWT token for authenticated user."""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.config.jwt_expiration_hours)

        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": self.rbac.get_user_permissions(user),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        token = jwt_lib.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

        access_token = AccessToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at.isoformat(),
            issued_at=now.isoformat(),
            permissions=payload["permissions"],
        )

        # Store active token
        self._active_tokens[token] = access_token

        return access_token

    def validate_token(self, token: str) -> Tuple[User, List[str]]:
        """Validate JWT token and return user with permissions."""
        try:
            payload = jwt_lib.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            user_id = payload["sub"]
            user = self._users.get(user_id)

            if not user or not user.is_active:
                raise AuthError("Invalid token")

            permissions = payload.get("permissions", [])
            return user, permissions

        except jwt_lib.ExpiredSignatureError:
            raise AuthError("Token expired")
        except (jwt_lib.InvalidTokenError, jwt_lib.DecodeError):
            raise AuthError("Invalid token")

    def revoke_token(self, token: str) -> None:
        """Revoke an access token."""
        if token in self._active_tokens:
            del self._active_tokens[token]

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def update_user(self, user_id: str, **updates) -> User:
        """Update user information."""
        user = self._users.get(user_id)
        if not user:
            raise AuthError("User not found")

        allowed_fields = ["full_name", "email", "is_active", "role"]
        for field in allowed_fields:
            if field in updates:
                if field == "role":
                    updates[field] = UserRole(updates[field])
                setattr(user, field, updates[field])

        user.updated_at = datetime.utcnow().isoformat()
        self._save_users()
        return user

    def delete_user(self, user_id: str) -> None:
        """Delete a user account."""
        if user_id in self._users:
            del self._users[user_id]
            self._save_users()

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        return [user.to_dict() for user in self._users.values()]

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> None:
        """Change user password."""
        user = self._users.get(user_id)
        if not user:
            raise AuthError("User not found")

        if not self._verify_password(old_password, user.password_hash):
            raise AuthError("Current password is incorrect")

        user.password_hash = self._hash_password(new_password)
        self._save_users()

    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return f"user_{int(time.time())}_{secrets.token_hex(4)}"

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt_lib.gensalt(rounds=self.config.bcrypt_rounds)
        hashed = bcrypt_lib.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt_lib.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )

    def _find_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """Find user by username or email."""
        for user in self._users.values():
            if user.username == username_or_email or user.email == username_or_email:
                return user
        return None

    def _record_failed_login(self, user: User) -> None:
        """Record failed login attempt."""
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= self.config.max_login_attempts:
            lockout_until = datetime.utcnow() + timedelta(
                minutes=self.config.lockout_duration_minutes
            )
            user.locked_until = lockout_until.isoformat()

        self._save_users()

    def _is_account_locked(self, user: User) -> bool:
        """Check if account is locked."""
        if user.locked_until:
            lockout_time = datetime.fromisoformat(user.locked_until)
            return datetime.utcnow() < lockout_time
        return False

    def _load_users(self) -> None:
        """Load users from storage."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        self._users[user_id] = User.from_dict(user_data)
        except Exception as e:
            print(f"Failed to load users: {e}")
            self._users = {}

    def _save_users(self) -> None:
        """Save users to storage."""
        try:
            data = {user_id: user.to_dict() for user_id, user in self._users.items()}

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save users: {e}")


# Singleton instances
_auth_manager: Optional[AuthManager] = None
_rbac_manager: Optional[RBACManager] = None


def get_auth_manager(
    config: Optional[AuthConfig] = None, storage_path: str = "./users.json"
) -> AuthManager:
    """Get or create auth manager singleton."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(config, storage_path)
    return _auth_manager


def get_rbac_manager() -> RBACManager:
    """Get or create RBAC manager singleton."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


# Utility functions for integration
def require_auth(permissions: Optional[List[str]] = None):
    """Decorator to require authentication and permissions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented in FastAPI middleware
            # For now, return the function as-is
            return func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Demo usage
    auth = get_auth_manager()

    # Create admin user
    try:
        admin = auth.create_user(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            password="admin123",
            role=UserRole.ADMIN,
        )
        print(f"Created admin user: {admin.username}")

        # Authenticate
        user = auth.authenticate_user("admin", "admin123")
        print(f"Authenticated user: {user.username}")

        # Generate token
        token = auth.generate_token(user)
        print(f"Generated token: {token.token[:50]}...")

        # Validate token
        validated_user, permissions = auth.validate_token(token.token)
        print(f"Validated user: {validated_user.username}")
        print(f"User permissions: {permissions[:3]}...")

    except Exception as e:
        print(f"Demo error: {e}")
