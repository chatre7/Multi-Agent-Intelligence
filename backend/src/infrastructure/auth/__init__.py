"""Authentication infrastructure."""

from .permissions import (
    Permission,
    has_permission,
    has_permission_set,
    parse_permissions,
    permissions_for_role,
    require_permission,
    require_permission_set,
    serialize_permissions,
)
from .security import (
    JwtConfig,
    create_access_token,
    get_claims_from_token,
    get_role_from_token,
    parse_bearer,
)

__all__ = [
    "JwtConfig",
    "Permission",
    "create_access_token",
    "get_claims_from_token",
    "has_permission",
    "has_permission_set",
    "get_role_from_token",
    "parse_bearer",
    "parse_permissions",
    "permissions_for_role",
    "require_permission",
    "require_permission_set",
    "serialize_permissions",
]
