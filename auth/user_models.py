"""
User Management API Models and Schemas

Pydantic models for the User Management REST API, providing data validation
and serialization for user-related operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system matching auth_system.py"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    USER = "user"
    AGENT = "agent"
    GUEST = "guest"


class User(BaseModel):
    """Core User model"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# Request Models
class UserCreate(BaseModel):
    """Request model for creating a new user"""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.USER

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        """Validate password complexity requirements"""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Request model for updating an existing user"""

    username: Optional[str] = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


class UserLogin(BaseModel):
    """Request model for user login"""

    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# Response Models
class UserResponse(BaseModel):
    """Response model for user data (excludes sensitive information)"""

    id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class TokenResponse(BaseModel):
    """Response model for authentication tokens"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Pagination Models
class PaginationParams(BaseModel):
    """Query parameters for pagination"""

    page: int = Field(1, gt=0)
    limit: int = Field(20, gt=0, le=100)
    role: Optional[UserRole] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""

    items: List[UserResponse]
    total: int
    page: int
    limit: int
    pages: int


# Error Models
class ErrorDetail(BaseModel):
    """Detailed error information"""

    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


# Health Check Model
class HealthResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    service: str = "user-management-api"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
