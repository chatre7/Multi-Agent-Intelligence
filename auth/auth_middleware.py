"""FastAPI Authentication Middleware and Dependencies.

Provides JWT authentication middleware and permission-based dependencies
for securing FastAPI endpoints.
"""

from typing import Optional, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth_system import (
    get_auth_manager,
    get_rbac_manager,
    AuthError,
    PermissionError,
    User,
)


security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Dependency for authenticated user."""

    def __init__(self, required_permissions: Optional[List[str]] = None):
        self.required_permissions = required_permissions or []

    async def __call__(
        self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> User:
        """Extract and validate user from JWT token."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        auth_manager = get_auth_manager()

        try:
            user, permissions = auth_manager.validate_token(credentials.credentials)

            # Check permissions if required
            if self.required_permissions:
                rbac_manager = get_rbac_manager()
                for permission in self.required_permissions:
                    if not rbac_manager.check_permission(user, permission):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Permission denied: {permission}",
                        )

            return user

        except AuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# Pre-configured dependencies
get_current_user = AuthenticatedUser()

# Permission-specific dependencies
get_admin_user = AuthenticatedUser(required_permissions=["user:manage", "role:manage"])
get_agent_manager = AuthenticatedUser(
    required_permissions=["agent:create", "agent:update"]
)
get_monitor_user = AuthenticatedUser(required_permissions=["monitor:read"])
get_tool_executor = AuthenticatedUser(required_permissions=["tool:execute"])
get_mcp_user = AuthenticatedUser(required_permissions=["mcp:access"])


class AuthMiddleware:
    """Authentication middleware for FastAPI.

    Can be added to FastAPI app for automatic JWT validation.
    """

    def __init__(self, exclude_paths: Optional[List[str]] = None):
        """Initialize middleware.

        Parameters
        ----------
        exclude_paths : Optional[List[str]]
            Paths to exclude from authentication
        """
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.auth_manager = get_auth_manager()

    async def __call__(self, request: Request, call_next):
        """Process request through authentication middleware."""
        # Skip authentication for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip authentication for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await self._unauthorized_response(
                "Missing or invalid Authorization header"
            )

        token = auth_header.split(" ")[1]

        try:
            # Validate token
            user, permissions = self.auth_manager.validate_token(token)

            # Add user and permissions to request state
            request.state.user = user
            request.state.permissions = permissions

        except AuthError as e:
            return await self._unauthorized_response(str(e))

        # Continue with request
        response = await call_next(request)
        return response

    async def _unauthorized_response(self, detail: str):
        """Return unauthorized response."""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
            headers={"WWW-Authenticate": "Bearer"},
        )


# Utility functions for endpoint protection
def check_user_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    rbac_manager = get_rbac_manager()
    return rbac_manager.check_permission(user, permission)


def require_permission(user: User, permission: str) -> None:
    """Require permission or raise HTTPException."""
    if not check_user_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )


# Token management utilities
def create_access_token(user: User) -> str:
    """Create access token for user."""
    auth_manager = get_auth_manager()
    token = auth_manager.generate_token(user)
    return token.token


def validate_token(token: str) -> tuple[User, List[str]]:
    """Validate token and return user with permissions."""
    auth_manager = get_auth_manager()
    return auth_manager.validate_token(token)


# User management utilities
def create_user(
    username: str, email: str, full_name: str, password: str, role: str = "user"
):
    """Create a new user."""
    from auth_system import UserRole

    auth_manager = get_auth_manager()
    role_enum = UserRole(role)
    return auth_manager.create_user(username, email, full_name, password, role_enum)


def authenticate_user(username: str, password: str) -> User:
    """Authenticate user and return User object."""
    auth_manager = get_auth_manager()
    return auth_manager.authenticate_user(username, password)


if __name__ == "__main__":
    # Demo FastAPI integration
    from fastapi import FastAPI

    app = FastAPI(title="Multi-Agent Auth Demo")

    # Add auth middleware
    auth_middleware = AuthMiddleware()
    app.middleware("http")(auth_middleware)

    @app.get("/protected")
    async def protected_endpoint(user: User = Depends(get_current_user)):
        """Protected endpoint requiring authentication."""
        return {
            "message": f"Hello {user.username}!",
            "role": user.role.value,
            "permissions": get_rbac_manager().get_user_permissions(user),
        }

    @app.get("/admin-only")
    async def admin_endpoint(user: User = Depends(get_admin_user)):
        """Admin-only endpoint."""
        return {"message": "Welcome to admin area!", "user": user.username}

    @app.get("/agent-tools")
    async def agent_tools(user: User = Depends(get_tool_executor)):
        """Endpoint for tool execution."""
        return {"message": "Tool execution allowed", "user": user.username}

    @app.post("/auth/login")
    async def login(username: str, password: str):
        """Login endpoint."""
        try:
            user = authenticate_user(username, password)
            token = create_access_token(user)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role.value,
                },
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    print(
        "FastAPI Auth Demo - use /auth/login to get token, then access protected endpoints"
    )
    print(
        "Example: curl -X POST 'http://localhost:8000/auth/login' -d 'username=admin&password=admin123'"
    )
    print(
        "Then: curl -H 'Authorization: Bearer <token>' http://localhost:8000/protected"
    )

    # Uncomment to run demo server
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8002)
