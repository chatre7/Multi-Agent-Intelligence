"""JWT auth utilities (optional mode)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt


@dataclass(frozen=True)
class JwtConfig:
    secret: str
    algorithm: str = "HS256"
    expires_minutes: int = 60 * 24


def create_access_token(
    *,
    subject: str,
    role: str,
    permissions: list[str] | None = None,
    config: JwtConfig,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "perms": permissions or [],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=config.expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, config.secret, algorithm=config.algorithm)


def decode_token(token: str, *, config: JwtConfig) -> dict[str, Any]:
    return jwt.decode(token, config.secret, algorithms=[config.algorithm])


def get_role_from_token(token: str, *, config: JwtConfig) -> str:
    try:
        payload = decode_token(token, config=config)
    except JWTError as exc:
        raise PermissionError("Invalid token") from exc
    role = payload.get("role")
    if not isinstance(role, str) or not role:
        raise PermissionError("Invalid token payload")
    return role.lower()


def get_claims_from_token(token: str, *, config: JwtConfig) -> dict[str, Any]:
    """Return decoded token claims."""
    try:
        return decode_token(token, config=config)
    except JWTError as exc:
        raise PermissionError("Invalid token") from exc


def parse_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme != "bearer" or not token:
        return None
    return token
