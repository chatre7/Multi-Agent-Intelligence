"""
User Management API Router

FastAPI router implementing all CRUD operations for user management
with proper authentication, authorization, and validation.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth_dependencies import (
    get_current_user,
    require_admin,
    require_ownership_or_admin,
    get_current_user_model,
    validate_user_exists,
)
from auth_service import get_user_service
from user_models import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRole,
    PaginatedResponse,
    PaginationParams,
    ErrorResponse,
    HealthResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user account. Requires admin privileges.",
)
async def create_user(
    user_data: UserCreate, current_user: dict = Depends(require_admin)
) -> UserResponse:
    """
    Create a new user account.

    - **username**: Unique username (3-50 chars, alphanumeric + underscore)
    - **email**: Valid email address
    - **password**: Password with complexity requirements (8+ chars, mixed case, digits)
    - **role**: User role (defaults to USER)

    Requires admin privileges.
    """
    user_service = get_user_service()

    try:
        # Check for existing user
        if user_service.username_or_email_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            )

        if user_service.username_or_email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

        # Create user
        user = user_service.create_user(user_data)

        logger.info(
            f"User created: {user.username} (ID: {user.id}) by admin {current_user.username}"
        )

        return UserResponse.from_orm(user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List Users",
    description="Get a paginated list of users. Requires admin privileges.",
)
async def list_users(
    page: int = Query(1, gt=0, description="Page number (1-based)"),
    limit: int = Query(20, gt=0, le=100, description="Items per page (max 100)"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    current_user: dict = Depends(require_admin),
) -> PaginatedResponse:
    """
    Get a paginated list of users.

    Query parameters:
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **role**: Optional role filter

    Requires admin privileges.
    """
    user_service = get_user_service()

    try:
        # Get filtered users
        all_users = user_service.list_users(role_filter=role)

        # Calculate pagination
        total = len(all_users)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # Slice for pagination
        paginated_users = all_users[start_idx:end_idx]
        total_pages = (total + limit - 1) // limit  # Ceiling division

        # Convert to response models
        user_responses = [UserResponse.from_orm(user) for user in paginated_users]

        return PaginatedResponse(
            items=user_responses, total=total, page=page, limit=limit, pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User Details",
    description="Get details of a specific user by ID. Users can view their own data, admins can view any user's data.",
)
async def get_user_details(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user: User = Depends(validate_user_exists),
) -> UserResponse:
    """
    Get details of a specific user.

    - **user_id**: UUID of the user to retrieve

    Users can access their own data, admins can access any user's data.
    """
    # Check permissions (ownership or admin)
    if current_user.id != user_id and UserRole(current_user.role) != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own data.",
        )

    return UserResponse.from_orm(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update user information. Users can update their own data, admins can update any user's data.",
)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    existing_user: User = Depends(validate_user_exists),
) -> UserResponse:
    """
    Update user information.

    - **user_id**: UUID of the user to update
    - **username**: New username (optional)
    - **email**: New email address (optional)
    - **role**: New user role (optional, admin only)

    Users can update their own data, admins can update any user's data.
    """
    user_service = get_user_service()

    # Check permissions
    is_admin = UserRole(current_user.role) == UserRole.ADMIN
    is_owner = current_user.id == user_id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only update your own data.",
        )

    # Non-admin users cannot change roles
    if not is_admin and update_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can change user roles.",
        )

    try:
        # Check for conflicts if username/email are being updated
        if update_data.username and update_data.username != existing_user.username:
            if user_service.username_or_email_exists(update_data.username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )

        if update_data.email and update_data.email != existing_user.email:
            if user_service.username_or_email_exists(update_data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
                )

        # Update user
        updated_user = user_service.update_user(user_id, update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info(
            f"User updated: {updated_user.username} (ID: {updated_user.id}) by {current_user.username}"
        )

        return UserResponse.from_orm(updated_user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete or deactivate a user account. Requires admin privileges.",
)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    user: User = Depends(validate_user_exists),
):
    """
    Delete or deactivate a user account.

    - **user_id**: UUID of the user to delete

    Requires admin privileges. This operation cannot be undone.
    """
    user_service = get_user_service()

    success = user_service.delete_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )

    logger.info(
        f"User deleted: {user.username} (ID: {user.id}) by admin {current_user.username}"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
    description="Get the profile information for the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_model),
) -> UserResponse:
    """
    Get the profile information for the currently authenticated user.

    Returns the user's own profile data without requiring an ID parameter.
    """
    return UserResponse.from_orm(current_user)


# Health check endpoint (not under /v1/users prefix)
health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring service status.
    """
    return HealthResponse()
