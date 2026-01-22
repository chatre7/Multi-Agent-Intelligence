"""Role -> permission mapping and enforcement helpers."""

from __future__ import annotations

from collections.abc import Iterable, Set
from enum import Enum


class Permission(Enum):
    """Application permissions (MVP)."""

    CHAT_SEND = "chat:send"
    CHAT_READ = "chat:read"
    CONFIG_RELOAD = "config:reload"
    DOMAIN_READ = "domain:read"
    HEALTH_READ = "health:read"
    METRICS_READ = "metrics:read"
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    TOOL_READ = "tool:read"
    TOOL_REQUEST = "tool:request"
    TOOL_APPROVE = "tool:approve"
    TOOL_REJECT = "tool:reject"
    TOOL_EXECUTE = "tool:execute"


ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "admin": frozenset(Permission),
    "developer": frozenset(
        {
            Permission.CHAT_SEND,
            Permission.CHAT_READ,
            Permission.CONFIG_RELOAD,
            Permission.DOMAIN_READ,
            Permission.HEALTH_READ,
            Permission.METRICS_READ,
            Permission.AGENT_READ,
            Permission.AGENT_WRITE,
            Permission.TOOL_READ,
            Permission.TOOL_REQUEST,
            Permission.TOOL_APPROVE,
            Permission.TOOL_REJECT,
            Permission.TOOL_EXECUTE,
        }
    ),
    "user": frozenset(
        {
            Permission.CHAT_SEND,
            Permission.CHAT_READ,
            Permission.TOOL_REQUEST,
        }
    ),
}


def permissions_for_role(role: str) -> frozenset[Permission]:
    """Return the permissions granted to a role."""
    role_key = (role or "").lower()
    return frozenset(ROLE_PERMISSIONS.get(role_key, frozenset()))


def serialize_permissions(permissions: Iterable[Permission]) -> list[str]:
    """Serialize permissions to string values."""
    return [p.value for p in permissions]


def parse_permissions(values: object) -> frozenset[Permission]:
    """Parse permission values from token claims."""
    if not isinstance(values, list):
        return frozenset()
    parsed = []
    for item in values:
        if isinstance(item, str):
            for perm in Permission:
                if perm.value == item:
                    parsed.append(perm)
                    break
    return frozenset(parsed)


def has_permission(role: str, permission: Permission) -> bool:
    """Return True if role includes the permission."""
    return permission in permissions_for_role(role)


def require_permission(role: str, permission: Permission) -> None:
    """Raise PermissionError if role doesn't have permission."""
    if not has_permission(role, permission):
        raise PermissionError(f"Missing permission: {permission.value}")


def has_permission_set(permissions: Set[Permission], permission: Permission) -> bool:
    """Return True if a permission set includes the permission."""
    return permission in permissions


def require_permission_set(
    permissions: Set[Permission], permission: Permission
) -> None:
    """Raise PermissionError if permission isn't present in the set."""
    if not has_permission_set(permissions, permission):
        raise PermissionError(f"Missing permission: {permission.value}")
