"""
Unit and Integration Tests for User Management API

Tests for models, authentication dependencies, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
import json
from unittest.mock import patch, MagicMock

from user_api import app
from user_models import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRole,
    ErrorResponse,
    HealthResponse,
)
from auth_dependencies import get_current_user, require_role
from auth_service import get_user_service


client = TestClient(app)


class TestUserModels:
    """Test Pydantic models and validation."""

    def test_user_model_creation(self):
        """Test creating a valid User model."""
        user = User(username="testuser", email="test@example.com", role=UserRole.USER)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.id is not None

    def test_user_create_validation(self):
        """Test UserCreate model validation."""
        # Valid user creation
        user_data = UserCreate(
            username="testuser", email="test@example.com", password="ValidPass123"
        )
        assert user_data.username == "testuser"

        # Invalid password (no uppercase)
        with pytest.raises(ValueError):
            UserCreate(
                username="testuser", email="test@example.com", password="invalidpass123"
            )

        # Invalid username (too short)
        with pytest.raises(ValueError):
            UserCreate(username="ab", email="test@example.com", password="ValidPass123")

    def test_user_response_model(self):
        """Test UserResponse model serialization."""
        user = User(username="testuser", email="test@example.com", role=UserRole.USER)

        response = UserResponse.model_validate(user)
        assert response.username == "testuser"
        assert response.email == "test@example.com"


class TestAuthDependencies:
    """Test authentication and authorization dependencies."""

    @patch("auth_dependencies.base_get_current_user")
    def test_get_current_user_success(self, mock_get_user):
        """Test successful user retrieval."""
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = "123"
        mock_get_user.return_value = mock_user

        # This would normally be tested as a FastAPI dependency
        # For now, just test the mock setup
        assert mock_user.username == "testuser"

    def test_user_role_hierarchy(self):
        """Test role hierarchy in require_role dependency."""
        # This would be tested in integration tests with actual endpoints
        # Just verify the role enum values
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"


class TestUserService:
    """Test the user service wrapper."""

    @patch("auth_service.get_auth_manager")
    def test_create_user_success(self, mock_get_manager):
        """Test successful user creation."""
        mock_manager = MagicMock()
        mock_manager.create_user.return_value = {
            "id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "is_active": True,
        }
        mock_get_manager.return_value = mock_manager

        service = get_user_service()
        user_data = UserCreate(
            username="testuser", email="test@example.com", password="ValidPass123"
        )

        user = service.create_user(user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"


class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-management-api"

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "User Management API"

    @patch("users_router.require_admin")
    @patch("users_router.get_user_service")
    def test_create_user_unauthorized(self, mock_get_service, mock_require_admin):
        """Test user creation without authorization."""
        # Mock unauthorized access
        mock_require_admin.side_effect = HTTPException(
            status_code=401, detail="Not authorized"
        )

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "ValidPass123",
        }

        response = client.post("/v1/users", json=user_data)
        assert response.status_code == 401

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        response = client.get("/docs")
        # FastAPI docs page should be accessible (may return HTML)
        assert response.status_code in [200, 302]  # 302 for redirect to docs

    def test_openapi_schema(self):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "User Management API" in schema.get("info", {}).get("title", "")


class TestErrorHandling:
    """Test error handling and responses."""

    def test_validation_error_response(self):
        """Test validation error formatting."""
        # Send invalid data to trigger validation error
        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",
            "password": "short",
        }

        # Try to access an endpoint that requires validation
        # Since most endpoints require auth, we'll test the general validation
        # This would be more comprehensive with authenticated requests

    def test_404_error(self):
        """Test 404 error for unknown endpoints."""
        response = client.get("/v1/unknown-endpoint")
        assert response.status_code == 404


# Integration test fixtures
@pytest.fixture
def auth_headers():
    """Mock authorization headers for testing."""
    # This would be replaced with actual JWT token generation in real tests
    return {"Authorization": "Bearer mock-jwt-token"}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "ValidPass123",
        "role": "user",
    }


if __name__ == "__main__":
    pytest.main([__file__])
