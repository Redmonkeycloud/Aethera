# Security Documentation

Comprehensive security system for authentication, authorization, and audit logging.

## Overview

The security system provides:
- **JWT-based Authentication**: Secure token-based authentication
- **RBAC (Role-Based Access Control)**: Fine-grained permission system
- **OAuth/OpenID Connect**: Support for Google, Microsoft, and Okta
- **Audit Logging**: Comprehensive tracking of all security-relevant actions

## Authentication

### User Registration

Register a new user account:

```bash
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

### User Login

Authenticate and receive JWT tokens:

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Access Tokens

Include the access token in the `Authorization` header:

```bash
GET /api/projects
Authorization: Bearer <access_token>
```

### Token Refresh

Refresh an expired access token:

```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

### Logout

Revoke refresh token:

```bash
POST /auth/logout
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

## OAuth/OpenID Connect

### Google OAuth

Authenticate with Google:

```bash
POST /auth/oauth/login
Content-Type: application/json

{
  "provider": "google",
  "access_token": "<google_access_token>"
}
```

### Microsoft Azure AD

Authenticate with Microsoft:

```bash
POST /auth/oauth/login
Content-Type: application/json

{
  "provider": "microsoft",
  "access_token": "<microsoft_access_token>"
}
```

### Okta

Authenticate with Okta:

```bash
POST /auth/oauth/login
Content-Type: application/json

{
  "provider": "okta",
  "access_token": "<okta_access_token>",
  "okta_domain": "dev-123456.okta.com"
}
```

## Role-Based Access Control (RBAC)

### Default Roles

1. **admin**: Full system access (all permissions)
2. **analyst**: Can create projects, run analyses, view results
3. **viewer**: Read-only access to projects and reports

### Default Permissions

- `projects:create` - Create new projects
- `projects:read` - View projects
- `projects:update` - Update projects
- `projects:delete` - Delete projects
- `runs:create` - Create analysis runs
- `runs:read` - View analysis runs
- `runs:update` - Update analysis runs
- `runs:delete` - Delete analysis runs
- `reports:read` - View reports
- `reports:export` - Export reports
- `models:read` - View model information
- `models:manage` - Manage model registry
- `users:read` - View user information
- `users:manage` - Manage users and roles
- `audit:read` - View audit logs

### Using Permissions in Routes

Protect routes with permission requirements:

```python
from backend.src.security.rbac import require_permission

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(require_permission("projects:create")),
):
    # User has 'projects:create' permission
    ...
```

### Using Roles in Routes

Protect routes with role requirements:

```python
from backend.src.security.rbac import require_role

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    # User has 'admin' role
    ...
```

### Managing Roles and Permissions

```python
from backend.src.security.rbac import RBACService
from backend.src.db.client import DatabaseClient

db = DatabaseClient(settings.postgres_dsn)
rbac = RBACService(db)

# Assign role to user
rbac.assign_role(user_id="...", role_name="analyst", assigned_by="admin_user_id")

# Grant permission to role
rbac.grant_permission(role_name="analyst", permission_name="projects:delete")

# Check user permissions
permissions = rbac.get_user_permissions(user_id="...")
has_permission = rbac.has_permission(user_id="...", permission="projects:create")
```

## Audit Logging

### Automatic Logging

All API requests are automatically logged with:
- User ID and username
- Action type (e.g., 'LOGIN', 'CREATE_PROJECT')
- Resource type and ID
- IP address and user agent
- Request method and path
- Response status
- Timestamp

### Querying Audit Logs

Get audit logs (requires `audit:read` permission):

```bash
GET /audit/logs?user_id=<user_id>&action=LOGIN&limit=100
Authorization: Bearer <access_token>
```

Query parameters:
- `user_id`: Filter by user ID
- `action`: Filter by action (e.g., 'LOGIN', 'CREATE_PROJECT')
- `resource_type`: Filter by resource type (e.g., 'project', 'run')
- `resource_id`: Filter by resource ID
- `limit`: Maximum number of results (default: 100)
- `offset`: Offset for pagination (default: 0)

### Manual Audit Logging

Log custom audit events:

```python
from backend.src.security.audit import audit_log

audit_log(
    action="CUSTOM_ACTION",
    user_id=current_user["id"],
    username=current_user["username"],
    resource_type="project",
    resource_id=project_id,
    metadata={"custom_field": "value"},
)
```

## Configuration

Security settings in `base_settings.py` or environment variables:

```python
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here  # CHANGE IN PRODUCTION!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Feature Flags
ENABLE_AUTHENTICATION=true
ENABLE_AUDIT_LOGGING=true

# OAuth Configuration (optional)
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_MICROSOFT_CLIENT_ID=your-microsoft-client-id
OAUTH_OKTA_DOMAIN=dev-123456.okta.com
```

## Database Schema

Security tables:
- `users`: User accounts
- `roles`: User roles
- `permissions`: Individual permissions
- `user_roles`: User-role assignments
- `role_permissions`: Role-permission assignments
- `refresh_tokens`: JWT refresh tokens
- `audit_logs`: Audit log entries

See `backend/src/db/schema.sql` for full schema.

## Public Endpoints

These endpoints don't require authentication:
- `/` - Health check
- `/docs` - API documentation
- `/openapi.json` - OpenAPI schema
- `/auth/login` - User login
- `/auth/register` - User registration
- `/auth/oauth/login` - OAuth login
- `/auth/refresh` - Token refresh
- `/metrics` - Prometheus metrics

All other endpoints require authentication.

## Security Best Practices

1. **Change JWT Secret**: Set a strong `JWT_SECRET_KEY` in production
2. **Use HTTPS**: Always use HTTPS in production
3. **Token Expiration**: Access tokens expire in 30 minutes by default
4. **Refresh Tokens**: Store refresh tokens securely (httpOnly cookies recommended)
5. **Password Policy**: Enforce strong passwords (minimum 8 characters)
6. **Audit Logs**: Regularly review audit logs for suspicious activity
7. **Role Management**: Assign minimal necessary permissions
8. **OAuth**: Configure OAuth providers with proper redirect URIs

## Troubleshooting

### "Not authenticated" Error

- Ensure `Authorization: Bearer <token>` header is present
- Check that token hasn't expired
- Verify token is valid (not revoked)

### "Permission required" Error

- User doesn't have required permission
- Check user's roles and role permissions
- Superusers have all permissions automatically

### OAuth Authentication Fails

- Verify access token is valid and not expired
- Check OAuth provider configuration
- Ensure correct provider name ('google', 'microsoft', 'okta')
- For Okta, provide `okta_domain`

