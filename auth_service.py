"""
Authentication Service Wrapper

Provides a clean interface for the User Management API to interact with
the existing auth_system.py, abstracting the underlying implementation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from auth_system import get_auth_manager, UserRole as AuthUserRole
from user_models import User, UserCreate, UserUpdate, UserResponse, UserRole


class UserManagementService:
    """Service class for user management operations"""

    def __init__(self):
        self.auth_manager = get_auth_manager()

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            User: Created user object

        Raises:
            ValueError: If user already exists or validation fails
        """
        try:
            # Convert to auth system format
            auth_user_data = {
                "username": user_data.username,
                "email": user_data.email,
                "password": user_data.password,
                "role": user_data.role.value,
            }

            # Create user via auth manager
            created_user = self.auth_manager.create_user(**auth_user_data)

            # Convert back to our User model
            return User(
                id=created_user.get("id", ""),
                username=created_user.get("username", user_data.username),
                email=created_user.get("email", user_data.email),
                role=UserRole(created_user.get("role", user_data.role.value)),
                created_at=created_user.get("created_at", datetime.utcnow()),
                updated_at=created_user.get("updated_at", datetime.utcnow()),
                is_active=created_user.get("is_active", True),
            )

        except Exception as e:
            raise ValueError(f"Failed to create user: {str(e)}")

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            Optional[User]: User object if found, None otherwise
        """
        user_data = self.auth_manager.get_user(user_id)
        if not user_data:
            return None

        return User(
            id=user_data.get("id", user_id),
            username=user_data.get("username", ""),
            email=user_data.get("email", ""),
            role=UserRole(user_data.get("role", "user")),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at"),
            is_active=user_data.get("is_active", True),
        )

    def get_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """
        Get a user by username or email.

        Args:
            username_or_email: Username or email to search for

        Returns:
            Optional[User]: User object if found, None otherwise
        """
        try:
            user_data = self.auth_manager._find_user_by_username_or_email(
                username_or_email
            )
            if not user_data:
                return None

            return User(
                id=user_data.get("id", ""),
                username=user_data.get("username", ""),
                email=user_data.get("email", ""),
                role=UserRole(user_data.get("role", "user")),
                created_at=user_data.get("created_at"),
                updated_at=user_data.get("updated_at"),
                is_active=user_data.get("is_active", True),
            )
        except Exception:
            return None

    def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """
        Update a user.

        Args:
            user_id: User ID to update
            update_data: Data to update

        Returns:
            Optional[User]: Updated user object if successful, None if user not found

        Raises:
            ValueError: If update fails
        """
        try:
            # Convert to dict, excluding None values
            update_dict = update_data.dict(exclude_unset=True)

            # Convert role enum to string if present
            if "role" in update_dict and isinstance(update_dict["role"], UserRole):
                update_dict["role"] = update_dict["role"].value

            # Update via auth manager
            updated_user = self.auth_manager.update_user(user_id, **update_dict)

            if not updated_user:
                return None

            # Convert back to our User model
            return User(
                id=updated_user.get("id", user_id),
                username=updated_user.get("username", ""),
                email=updated_user.get("email", ""),
                role=UserRole(updated_user.get("role", "user")),
                created_at=updated_user.get("created_at"),
                updated_at=updated_user.get("updated_at"),
                is_active=updated_user.get("is_active", True),
            )

        except Exception as e:
            raise ValueError(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """
        Delete/deactivate a user.

        Args:
            user_id: User ID to delete

        Returns:
            bool: True if deleted successfully, False if user not found
        """
        try:
            self.auth_manager.delete_user(user_id)
            return True
        except Exception:
            return False

    def list_users(self, role_filter: Optional[UserRole] = None) -> List[User]:
        """
        List all users, optionally filtered by role.

        Args:
            role_filter: Optional role to filter by

        Returns:
            List[User]: List of user objects
        """
        users_data = self.auth_manager.list_users()
        users = []

        for user_data in users_data:
            user_role = UserRole(user_data.get("role", "user"))

            # Apply role filter if specified
            if role_filter and user_role != role_filter:
                continue

            users.append(
                User(
                    id=user_data.get("id", ""),
                    username=user_data.get("username", ""),
                    email=user_data.get("email", ""),
                    role=user_role,
                    created_at=user_data.get("created_at"),
                    updated_at=user_data.get("updated_at"),
                    is_active=user_data.get("is_active", True),
                )
            )

        return users

    def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user with username/email and password.

        Args:
            username_or_email: Username or email
            password: Password

        Returns:
            Optional[User]: User object if authentication successful, None otherwise
        """
        try:
            authenticated_user = self.auth_manager.authenticate_user(
                username_or_email, password
            )
            if not authenticated_user:
                return None

            return User(
                id=authenticated_user.get("id", ""),
                username=authenticated_user.get("username", ""),
                email=authenticated_user.get("email", ""),
                role=UserRole(authenticated_user.get("role", "user")),
                created_at=authenticated_user.get("created_at"),
                updated_at=authenticated_user.get("updated_at"),
                is_active=authenticated_user.get("is_active", True),
            )
        except Exception:
            return None

    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists.

        Args:
            user_id: User ID to check

        Returns:
            bool: True if user exists, False otherwise
        """
        return self.get_user(user_id) is not None

    def username_or_email_exists(self, username_or_email: str) -> bool:
        """
        Check if a username or email already exists.

        Args:
            username_or_email: Username or email to check

        Returns:
            bool: True if exists, False otherwise
        """
        return self.get_user_by_username_or_email(username_or_email) is not None


# Global service instance
_user_service = None


def get_user_service() -> UserManagementService:
    """Get the singleton user management service instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserManagementService()
    return _user_service
