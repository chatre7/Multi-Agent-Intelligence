"""User Management REST API Module.

Provides comprehensive CRUD operations for user management with JWT-based
authentication and role-based access control. Integrates with the existing
auth_system.py for secure user operations.

Features:
- Full CRUD operations for users
- Role-based permissions (ADMIN, DEVELOPER, OPERATOR, USER, AGENT, GUEST)
- JWT token validation on all protected endpoints
- Pagination support for user listings
- Input validation and security measures
- OpenAPI 3.0 documentation
- Production-ready error handling and logging
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, field_validator
from pydantic.types import constr, conbytes

from auth_system import (
    get_auth_manager,
    get_rbac_manager,
    UserRole,
    AuthError,
    User,
)
from auth_middleware import get_current_user, get_admin_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - User not found"},
        422: {"description": "Validation Error - Invalid input data"},
        500: {"description": "Internal Server Error"},
    },
)


# ==========================================
# PYDANTIC MODELS
# ==========================================


class UserBase(BaseModel):
    """Base user model with common fields."""

    username: constr(min_length=3, max_length=50, strip_whitespace=True) = Field(
        ..., description="Unique username (3-50 characters)"
    )
    email: str = Field(
        ...,
        description="Valid email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    full_name: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., description="Full display name (1-100 characters)"
    )
    role: str = Field(
        ..., description="User role (admin, developer, operator, user, agent, guest)"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        allowed_roles = [role.value for role in UserRole]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: constr(min_length=8, max_length=128) = Field(
        ..., description="Password (8-128 characters)"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Basic password strength validation."""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Model for updating an existing user."""

    username: Optional[constr(min_length=3, max_length=50, strip_whitespace=True)] = (
        Field(None, description="Username (optional)")
    )
    email: Optional[str] = Field(
        None,
        description="Email address (optional)",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    full_name: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = (
        Field(None, description="Full display name (optional)")
    )
    role: Optional[str] = Field(None, description="User role (optional)")
    is_active: Optional[bool] = Field(
        None, description="Account active status (optional)"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        if v is not None:
            allowed_roles = [role.value for role in UserRole]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserResponse(BaseModel):
    """Response model for user data."""

    id: str = Field(..., description="Unique user ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full display name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")


class UserListResponse(BaseModel):
    """Response model for paginated user list."""

    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of users per page")
    total_pages: int = Field(..., description="Total number of pages")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class PasswordChangeRequest(BaseModel):
    """Model for password change requests."""

    current_password: str = Field(..., description="Current password")
    new_password: constr(min_length=8, max_length=128) = Field(
        ..., description="New password (8-128 characters)"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Basic password strength validation."""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ==========================================
# UTILITY FUNCTIONS
# ==========================================


def _convert_user_to_response(user: User) -> UserResponse:
    """Convert User dataclass to UserResponse model."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=getattr(user, "full_name", user.username),  # Fallback for older users
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=getattr(user, "updated_at", None),
        last_login=user.last_login,
    )


def _check_self_or_admin_access(current_user: User, target_user_id: str) -> None:
    """Check if user can access target user (self or admin)."""
    rbac_manager = get_rbac_manager()

    # Admin can access all users
    if rbac_manager.check_permission(current_user, "user:manage"):
        return

    # Users can access their own profile
    if current_user.id == target_user_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: can only access your own profile or require admin privileges",
    )


def _check_admin_only(current_user: User) -> None:
    """Check if user has admin privileges."""
    rbac_manager = get_rbac_manager()
    if not rbac_manager.check_permission(current_user, "user:manage"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


# ==========================================
# API ENDPOINTS
# ==========================================


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user account. Requires admin privileges.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Bad request - validation error or user already exists"},
        403: {"description": "Forbidden - admin privileges required"},
    },
)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
) -> UserResponse:
    """Create a new user account (admin only)."""
    try:
        auth_manager = get_auth_manager()

        # Convert role string to enum
        role_enum = UserRole(user_data.role)

        # Create the user
        new_user = auth_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password,
            role=role_enum,
        )

        logger.info(f"User created: {new_user.username} by {current_user.username}")

        return _convert_user_to_response(new_user)

    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating user",
        )


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List Users",
    description="Get a paginated list of all users. Requires admin privileges.",
    responses={
        200: {"description": "Users retrieved successfully"},
        403: {"description": "Forbidden - admin privileges required"},
    },
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Users per page (1-100)"),
    current_user: User = Depends(get_admin_user),
) -> UserListResponse:
    """List all users with pagination (admin only)."""
    try:
        auth_manager = get_auth_manager()
        all_users = auth_manager.list_users()

        # Calculate pagination
        total_users = len(all_users)
        total_pages = (total_users + page_size - 1) // page_size  # Ceiling division

        # Get users for current page
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_users = all_users[start_idx:end_idx]

        # Convert to response models
        user_responses = []
        for user_data in page_users:
            # Convert dict back to User object for response conversion
            user_obj = User.from_dict(user_data)
            user_responses.append(_convert_user_to_response(user_obj))

        return UserListResponse(
            users=user_responses,
            total=total_users,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving users",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
    description="Get the current authenticated user's profile information.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Unauthorized - authentication required"},
    },
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user's profile."""
    return _convert_user_to_response(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User Details",
    description="Get detailed information about a specific user. Users can access their own profile, admins can access all profiles.",
    responses={
        200: {"description": "User details retrieved successfully"},
        403: {"description": "Forbidden - access denied"},
        404: {"description": "User not found"},
    },
)
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get user details (self or admin)."""
    try:
        # Check permissions
        _check_self_or_admin_access(current_user, user_id)

        auth_manager = get_auth_manager()
        user = auth_manager.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return _convert_user_to_response(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving user",
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update user information. Users can update their own profile, admins can update all profiles.",
    responses={
        200: {"description": "User updated successfully"},
        403: {"description": "Forbidden - access denied"},
        404: {"description": "User not found"},
        400: {"description": "Bad request - validation error"},
    },
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Update user information (self or admin)."""
    try:
        # Check permissions
        _check_self_or_admin_access(current_user, user_id)

        auth_manager = get_auth_manager()
        user = auth_manager.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prepare update data
        update_data = user_update.dict(exclude_unset=True)

        # Convert role string to enum if provided
        if "role" in update_data:
            update_data["role"] = UserRole(update_data["role"])

        # Update the user
        updated_user = auth_manager.update_user(user_id, **update_data)

        logger.info(f"User updated: {updated_user.username} by {current_user.username}")

        return _convert_user_to_response(updated_user)

    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating user",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete a user account. Requires admin privileges. Users cannot delete themselves.",
    responses={
        204: {"description": "User deleted successfully"},
        403: {
            "description": "Forbidden - admin privileges required or cannot delete self"
        },
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
) -> None:
    """Delete user (admin only, cannot delete self)."""
    try:
        # Prevent self-deletion
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete your own account",
            )

        auth_manager = get_auth_manager()
        user = auth_manager.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Delete the user
        auth_manager.delete_user(user_id)

        logger.info(f"User deleted: {user.username} by {current_user.username}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting user",
        )


@router.post(
    "/{user_id}/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change user password. Users can change their own password, admins can change any password.",
    responses={
        200: {"description": "Password changed successfully"},
        400: {
            "description": "Bad request - current password incorrect or validation error"
        },
        403: {"description": "Forbidden - access denied"},
        404: {"description": "User not found"},
    },
)
async def change_password(
    user_id: str,
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Change user password (self or admin)."""
    try:
        # Check permissions
        _check_self_or_admin_access(current_user, user_id)

        auth_manager = get_auth_manager()

        # For non-admin users, verify current password
        rbac_manager = get_rbac_manager()
        is_admin = rbac_manager.check_permission(current_user, "user:manage")

        if not is_admin and current_user.id == user_id:
            # User changing their own password - verify current password
            auth_manager.change_password(
                user_id, password_change.current_password, password_change.new_password
            )
        elif is_admin:
            # Admin changing password - no need to verify current password
            user = auth_manager.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            # Directly set new password hash
            user.password_hash = auth_manager._hash_password(
                password_change.new_password
            )
            auth_manager._save_users()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        logger.info(f"Password changed for user {user_id} by {current_user.username}")

        return {"message": "Password changed successfully"}

    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while changing password",
        )


# ==========================================
# HEALTH CHECK ENDPOINT (for this module)
# ==========================================


@router.get(
    "/health",
    summary="User Management API Health Check",
    description="Check if the user management API is operational.",
    responses={
        200: {"description": "API is healthy"},
        500: {"description": "API is unhealthy"},
    },
    dependencies=[],  # No authentication required for health check
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for user management API."""
    try:
        auth_manager = get_auth_manager()
        user_count = len(auth_manager.list_users())

        return {
            "status": "healthy",
            "service": "user-management-api",
            "timestamp": datetime.utcnow().isoformat(),
            "user_count": user_count,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User management API is unhealthy",
        )


# ==========================================
# MAIN APPLICATION FACTORY
# ==========================================


def create_user_management_app() -> APIRouter:
    """Create and return the user management API router.

    Returns
    -------
    APIRouter
        Configured FastAPI router with all user management endpoints.
    """
    return router


if __name__ == "__main__":
    # Demo usage
    from fastapi import FastAPI

    app = FastAPI(
        title="Multi-Agent Intelligence - User Management API",
        description="REST API for user management with JWT authentication and RBAC",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include the user management router
    app.include_router(router)

    print("User Management API Demo")
    print("Access Swagger UI at: http://localhost:8000/docs")
    print("Access ReDoc at: http://localhost:8000/redoc")
    print("API Health Check at: http://localhost:8000/users/health")

    # Uncomment to run demo server
    # uvicorn.run(app, host="0.0.0.0", port=8000)
