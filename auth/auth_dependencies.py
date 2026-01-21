"""
Authentication and Authorization Dependencies for User Management API

FastAPI dependencies for JWT authentication and role-based access control,
integrating with the existing auth_system and auth_middleware.
"""

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth_middleware import get_current_user as base_get_current_user, AuthenticatedUser
from auth_system import get_auth_manager, UserRole
from auth.user_models import User, UserResponse


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Args:
        credentials: JWT token from Authorization header

    Returns:
        AuthenticatedUser: The authenticated user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Use existing middleware to validate token and get user
        user = await base_get_current_user(credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_model(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> User:
    """
    Get the full User model for the current authenticated user.

    Args:
        current_user: The authenticated user from JWT

    Returns:
        User: Full user model from auth system

    Raises:
        HTTPException: If user not found in system
    """
    auth_manager = get_auth_manager()
    user_data = auth_manager.get_user(current_user.id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Convert auth system user to our User model
    return User(
        id=user_data.get("id", current_user.id),
        username=user_data.get("username", current_user.username),
        email=user_data.get("email", ""),
        role=UserRole(user_data.get("role", "user")),
        created_at=user_data.get("created_at"),
        updated_at=user_data.get("updated_at"),
        is_active=user_data.get("is_active", True),
    )


def require_role(required_role: UserRole) -> Callable:
    """
    Create a dependency that requires a specific role.

    Args:
        required_role: The minimum role required

    Returns:
        Callable: FastAPI dependency function
    """

    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        """
        Check if the current user has the required role.

        Role hierarchy (from lowest to highest):
        GUEST -> USER -> AGENT -> OPERATOR -> DEVELOPER -> ADMIN
        """
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.AGENT: 2,
            UserRole.OPERATOR: 3,
            UserRole.DEVELOPER: 4,
            UserRole.ADMIN: 5,
        }

        user_role = UserRole(current_user.role)
        required_level = role_hierarchy.get(required_role, 0)
        user_level = role_hierarchy.get(user_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}, your role: {user_role.value}",
            )

        return current_user

    return role_checker


# Pre-defined role dependencies for common use cases
require_admin = require_role(UserRole.ADMIN)
require_developer = require_role(UserRole.DEVELOPER)
require_operator = require_role(UserRole.OPERATOR)


def require_ownership_or_admin(user_id_param: str) -> Callable:
    """
    Create a dependency that allows access to own data or admin access to any data.

    Args:
        user_id_param: The parameter name containing the user ID to check

    Returns:
        Callable: FastAPI dependency function
    """

    async def ownership_checker(
        user_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        """
        Check if the current user owns the resource or is an admin.
        """
        # Admins can access anything
        if UserRole(current_user.role) == UserRole.ADMIN:
            return current_user

        # Users can only access their own data
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own data.",
            )

        return current_user

    return ownership_checker


async def validate_user_exists(user_id: str) -> User:
    """
    Dependency to validate that a user exists and return their data.

    Args:
        user_id: The user ID to validate

    Returns:
        User: The user model if found

    Raises:
        HTTPException: If user not found
    """
    auth_manager = get_auth_manager()
    user_data = auth_manager.get_user(user_id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return User(
        id=user_data.get("id", user_id),
        username=user_data.get("username", ""),
        email=user_data.get("email", ""),
        role=UserRole(user_data.get("role", "user")),
        created_at=user_data.get("created_at"),
        updated_at=user_data.get("updated_at"),
        is_active=user_data.get("is_active", True),
    )


# Convenience dependencies
get_admin_user = require_admin
get_current_user_response = get_current_user_model
