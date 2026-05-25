---
name: "oauth2-add-endpoint"
description: "Add new protected endpoints to the Resource Server following OAuth2 token validation patterns"
patterns:
  - "add.*endpoint"
  - "add.*protected api"
  - "create.*resource"
---

# Adding Protected Endpoints to OAuth2 Resource Server

## Quick Summary

To add a new protected endpoint that requires OAuth2 token validation:

1. Define route in [resource-server/routes.py](resource-server/routes.py)
2. Use `@require_oauth2` decorator for automatic token validation
3. Access user context via `request.oauth2_user`
4. Add tests in [tests/resource_server/](tests/resource_server/)

## Pattern: Protected Endpoint

```python
# resource-server/routes.py
from fastapi import APIRouter, Request, HTTPException
from security import require_oauth2

router = APIRouter()

@router.get("/api/user/profile")
@require_oauth2
async def get_user_profile(request: Request):
    """
    Get user profile information.
    
    Requires: Bearer token in Authorization header
    Returns: User profile data
    """
    user = request.oauth2_user  # Automatically injected by @require_oauth2
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }
```

## How Token Validation Works

1. Client sends request with `Authorization: Bearer <token>`
2. `@require_oauth2` decorator extracts token from header
3. Token is validated (signature, expiry, scopes)
4. User object is injected into request context
5. Endpoint handler executes and accesses `request.oauth2_user`

## Pattern: Endpoint with Scope Requirements

Some endpoints may require specific OAuth2 scopes:

```python
@router.delete("/api/user/data")
@require_oauth2(scopes=["user:delete"])
async def delete_user_data(request: Request):
    """Delete all user data - requires 'user:delete' scope."""
    user = request.oauth2_user
    # Implementation...
```

## Pattern: Admin-Only Endpoint

```python
@router.get("/api/admin/users")
@require_oauth2
async def list_all_users(request: Request):
    """List all users - admin only."""
    user = request.oauth2_user
    
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    # Implementation...
```

## Testing Protected Endpoints

```python
# tests/resource_server/test_endpoints.py
import pytest
from auth_client import create_test_token

def test_get_profile_with_valid_token():
    """Test profile endpoint with valid OAuth2 token."""
    token = create_test_token(user_id=1)
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "alice"

def test_get_profile_without_token():
    """Test profile endpoint without token - should fail."""
    response = client.get("/api/user/profile")
    assert response.status_code == 401
    assert "Bearer token required" in response.json()["detail"]

def test_get_profile_with_expired_token():
    """Test profile endpoint with expired token - should fail."""
    token = create_expired_token()
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "Token expired" in response.json()["detail"]
```

## Token Validation Modes

The resource server can validate tokens in two ways (set via `TOKEN_VALIDATION_MODE` in `.env`):

### Mode 1: JWT Validation (Default)
- Token is a JWT signed by Authorization Server
- Resource Server validates signature locally using shared secret
- No network call needed - fast!
- Requires `AUTH_SERVER_SECRET_KEY` in environment

### Mode 2: Token Introspection
- Resource Server calls Authorization Server's `/introspect` endpoint
- Slower but handles revoked tokens and complex scenarios
- Set `TOKEN_VALIDATION_MODE=introspection` in `.env`

```python
# Both modes use same @require_oauth2 decorator
# Mode selection is automatic based on TOKEN_VALIDATION_MODE
```

## Common Patterns

### Get Paginated Results
```python
@router.get("/api/user/documents")
@require_oauth2
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10
):
    """Get user's documents with pagination."""
    user = request.oauth2_user
    documents = db.query(Document)\
        .filter(Document.user_id == user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [doc.to_dict() for doc in documents]
```

### Create Resource
```python
@router.post("/api/user/documents")
@require_oauth2
async def create_document(
    request: Request,
    doc_input: DocumentCreate
):
    """Create new document for user."""
    user = request.oauth2_user
    
    document = Document(
        title=doc_input.title,
        content=doc_input.content,
        user_id=user.id
    )
    db.add(document)
    db.commit()
    
    return document.to_dict()
```

### Filter by User
```python
@router.get("/api/user/settings")
@require_oauth2
async def get_user_settings(request: Request):
    """Get settings specific to authenticated user."""
    user = request.oauth2_user
    
    settings = db.query(UserSettings)\
        .filter(UserSettings.user_id == user.id)\
        .first()
    
    if not settings:
        raise HTTPException(
            status_code=404,
            detail="User settings not found"
        )
    
    return settings.to_dict()
```

## Error Handling

Standard OAuth2 error responses (auto-generated by `@require_oauth2`):

| Error | Status | Cause |
|-------|--------|-------|
| `invalid_token` | 401 | Malformed or invalid token |
| `expired_token` | 401 | Token has expired |
| `insufficient_scope` | 403 | Token lacks required scopes |
| `invalid_request` | 400 | Missing Authorization header |

To return custom errors:
```python
@router.get("/api/resource")
@require_oauth2
async def get_resource(request: Request):
    user = request.oauth2_user
    
    # Custom business logic validation
    if user.subscription_expired:
        raise HTTPException(
            status_code=402,
            detail="Payment required - subscription expired"
        )
    
    return {"data": "resource"}
```

## Debugging Token Issues

To debug token validation:

1. **Enable debug logging**
   ```bash
   # In .env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. **Check token contents**
   ```bash
   # Decode JWT at jwt.io
   # Or use Python:
   import jwt
   token = "eyJ..."
   decoded = jwt.decode(token, verify=False)
   print(decoded)
   ```

3. **Test token validation**
   ```bash
   # Call introspection endpoint
   curl -X POST http://localhost:5000/introspect \
     -d "token=eyJ..." \
     -H "Content-Type: application/x-www-form-urlencoded"
   ```

4. **View logs**
   ```bash
   make logs-resource
   ```

## File References

- [Token validation logic](resource-server/security.py)
- [Example endpoints](resource-server/routes.py)
- [Tests](tests/resource_server/)
- [Configuration](resource-server/config.py)
