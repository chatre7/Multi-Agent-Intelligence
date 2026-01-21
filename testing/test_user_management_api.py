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

    # Add auth middleware with /health in exclude paths
    auth_middleware = AuthMiddleware(
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",  # Exclude health check from auth
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
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "user-management-api"
    assert "timestamp" in data
    assert "version" in data


def test_create_user_invalid_data(client):
    """Test create user with invalid data requires auth."""
    # Test missing required fields - should fail auth before validation
    response = client.post("/users/", json={})
    # Auth middleware blocks before validation, so expect 401
    assert response.status_code == 401

    # Test weak password - also blocked by auth
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
    assert response.status_code == 401


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
    """Test that router exists and has correct prefix."""
    from apis.users_router import router
    assert router is not None
    assert router.prefix == "/v1/users"
