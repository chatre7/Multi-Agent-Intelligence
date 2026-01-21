# User Management API

A REST API for managing users in the Multi-Agent Intelligence system, built with FastAPI and featuring JWT authentication, role-based access control (RBAC), and comprehensive CRUD operations.

## Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Six user roles with hierarchical permissions
- **Complete CRUD Operations**: Create, read, update, delete users
- **Input Validation**: Comprehensive Pydantic validation
- **Auto-Documentation**: Interactive OpenAPI/Swagger docs
- **Error Handling**: Consistent error responses
- **Health Monitoring**: Service health check endpoint

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
python user_api.py
```

The API will be available at `http://localhost:8000`

### 3. Access Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
All endpoints except health check require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### User Management

| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| POST | `/v1/users` | Create new user | ADMIN |
| GET | `/v1/users` | List users (paginated) | ADMIN |
| GET | `/v1/users/{user_id}` | Get user details | ADMIN or owner |
| PUT | `/v1/users/{user_id}` | Update user | ADMIN or owner |
| DELETE | `/v1/users/{user_id}` | Delete user | ADMIN |
| GET | `/v1/users/me` | Get current user profile | Any authenticated user |

### Health & Monitoring

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/health` | Service health check | None |
| GET | `/` | API information | None |

## User Roles & Permissions

### Role Hierarchy
1. **GUEST** - Read-only access to public information
2. **USER** - Access to own profile only
3. **AGENT** - Programmatic access with limited permissions
4. **OPERATOR** - Operational permissions
5. **DEVELOPER** - Development and testing permissions
6. **ADMIN** - Full system access

### Permission Matrix

| Operation | GUEST | USER | AGENT | OPERATOR | DEVELOPER | ADMIN |
|-----------|-------|------|-------|----------|-----------|-------|
| View own profile | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Update own profile | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View all users | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Create users | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Update any user | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Delete users | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## Request/Response Examples

### Create User (ADMIN only)
```bash
POST /v1/users
Authorization: Bearer <admin-jwt-token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123",
  "role": "user"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "newuser",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-01-21T10:30:00Z",
  "updated_at": "2026-01-21T10:30:00Z"
}
```

### List Users (ADMIN only)
```bash
GET /v1/users?page=1&limit=10&role=user
Authorization: Bearer <admin-jwt-token>
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "user1",
      "email": "user1@example.com",
      "role": "user",
      "created_at": "2026-01-21T09:00:00Z",
      "updated_at": "2026-01-21T09:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

### Get Current User Profile
```bash
GET /v1/users/me
Authorization: Bearer <user-jwt-token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "currentuser",
  "email": "current@example.com",
  "role": "user",
  "created_at": "2026-01-21T08:00:00Z",
  "updated_at": "2026-01-21T08:00:00Z"
}
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Field-specific error message"
    }
  ],
  "timestamp": "2026-01-21T10:30:00Z"
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | validation_error | Input validation failed |
| 401 | http_error | Authentication required |
| 403 | http_error | Insufficient permissions |
| 404 | http_error | Resource not found |
| 409 | http_error | Resource conflict (duplicate user) |
| 422 | validation_error | Request validation failed |
| 500 | internal_error | Server error |

## Data Models

### User Roles
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    USER = "user"
    AGENT = "agent"
    GUEST = "guest"
```

### Request Schemas
- **UserCreate**: username, email, password, role
- **UserUpdate**: username?, email?, role?
- **PaginationParams**: page, limit, role?

### Response Schemas
- **UserResponse**: id, username, email, role, created_at, updated_at
- **PaginatedResponse**: items[], total, page, limit, pages
- **ErrorResponse**: error, message, details[], timestamp

## Validation Rules

### Username
- 3-50 characters
- Alphanumeric characters and underscores only
- Must be unique

### Email
- Valid email format
- Must be unique

### Password
- Minimum 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one digit

## Testing

### Run Unit Tests
```bash
pytest test_user_api.py -v
```

### Run with Coverage
```bash
pytest test_user_api.py --cov=user_api --cov-report=html
```

### Manual Testing
Use the interactive docs at `/docs` or tools like curl/Postman.

## Security Considerations

- **JWT Expiration**: Tokens expire and require refresh
- **Password Hashing**: Passwords are hashed with bcrypt
- **Input Sanitization**: All inputs are validated and sanitized
- **Rate Limiting**: Consider implementing rate limiting for production
- **Audit Logging**: All user operations are logged

## Deployment

### Development
```bash
python user_api.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn user_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "user_api.py"]
```

## Architecture

The API is built with a modular architecture:

- **user_api.py**: Main FastAPI application
- **users_router.py**: API route definitions
- **auth_dependencies.py**: Authentication/authorization logic
- **auth_service.py**: Service layer interfacing with auth_system
- **user_models.py**: Pydantic data models and validation

## Contributing

1. Follow the established SpecKit constitution
2. Add tests for new functionality
3. Update API documentation
4. Ensure all linting passes: `ruff check . && ruff format .`

## License

This API is part of the Multi-Agent Intelligence system and follows the same licensing terms.