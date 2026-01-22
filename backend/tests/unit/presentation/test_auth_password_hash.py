"""TDD tests for hashed password support in AUTH_USERS."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient
from passlib.context import CryptContext


def test_login_accepts_hashed_passwords() -> None:
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["AUTH_SECRET"] = "test-secret"

    # Use pbkdf2_sha256 to avoid optional bcrypt backend issues in test env.
    ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    hashed = ctx.hash("s3cret")

    os.environ["AUTH_USERS"] = f"developer:{hashed}:developer"

    from src.presentation.api.app import create_app

    client = TestClient(create_app())
    resp = client.post(
        "/v1/auth/login", json={"username": "developer", "password": "s3cret"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]
