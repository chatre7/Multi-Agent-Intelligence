"""
User Management API Application

FastAPI application for user management with JWT authentication,
RBAC authorization, and comprehensive CRUD operations.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from users_router import router as users_router, health_router
from user_models import ErrorResponse, ErrorDetail

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting User Management API")

    # Startup logic here
    logger.info("User Management API startup complete")

    yield

    # Shutdown logic here
    logger.info("Shutting down User Management API")


# Create FastAPI application
app = FastAPI(
    title="User Management API",
    description="""
    REST API for managing users in the Multi-Agent Intelligence system.

    ## Features
    - JWT-based authentication
    - Role-based access control (RBAC)
    - Complete CRUD operations
    - Comprehensive input validation
    - Auto-generated OpenAPI documentation

    ## Authentication
    Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```

    ## Roles
    - **ADMIN**: Full access to all operations
    - **USER**: Access to own profile only
    - **GUEST/DEVELOPER/OPERATOR/AGENT**: Various permission levels
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed field information."""
    details = []
    for error in exc.errors():
        details.append(
            ErrorDetail(
                field=".".join(str(loc) for loc in error["loc"]), message=error["msg"]
            )
        )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error", message="Input validation failed", details=details
        ).model_dump(),
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        details.append(
            ErrorDetail(
                field=".".join(str(loc) for loc in error["loc"]), message=error["msg"]
            )
        )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error", message="Data validation failed", details=details
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    # Create error response manually to avoid datetime serialization issues
    error_data = {
        "error": "internal_error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.utcnow().isoformat(),
    }

    return JSONResponse(
        status_code=500,
        content=error_data,
    )


# Include routers
app.include_router(users_router)
app.include_router(health_router)


# Root endpoint
@app.get(
    "/", summary="API Root", description="Welcome endpoint for the User Management API"
)
async def root():
    """Get API information."""
    return {
        "service": "User Management API",
        "version": "1.0.0",
        "description": "REST API for user management with JWT authentication and RBAC",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn for development
    uvicorn.run(
        "user_api:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
