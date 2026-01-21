"""Tests for User Management API."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apis.users_router import router, health_router
from auth.auth_middleware import AuthMiddleware


@pytest.fixture
def test_app():
    """Create test FastAPI app with user management router and auth middleware."""
    app = FastAPI()
    app.include_router(router)
    app.include_router(health_router)

    # Add auth middleware with /users/health in exclude paths
    auth_middleware = AuthMiddleware(
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/users/health",  # Exclude health check from auth
        ]
    )
    app.middleware("http")(auth_middleware)

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/users/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "user-management-api"
    assert "user_count" in data
    assert "timestamp" in data


def test_create_user_invalid_data(client):
    """Test create user with invalid data."""
    # Test missing required fields
    response = client.post("/users/", json={})
    assert response.status_code == 422  # Validation error

    # Test weak password
    response = client.post(
        "/users/",
        json={
            "username": "test",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "user",
            "password": "123",  # Too short and weak
        },
    )
    assert response.status_code == 422


def test_get_current_user_unauthorized(client):
    """Test accessing protected endpoint without auth."""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_list_users_unauthorized(client):
    """Test listing users without auth."""
    response = client.get("/users/")
    assert response.status_code == 401


def test_get_user_unauthorized(client):
    """Test getting user details without auth."""
    response = client.get("/users/some-id")
    assert response.status_code == 401


def test_router_creation():
    """Test that router can be created."""
    router = create_user_management_app()
    assert router is not None
    assert router.prefix == "/users"
