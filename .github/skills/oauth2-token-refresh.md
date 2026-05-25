---
name: "oauth2-token-refresh"
description: "Implement and manage OAuth2 token refresh logic to maintain continuous API access"
patterns:
  - "implement.*refresh"
  - "handle.*token.*expir"
  - "refresh.*token"
  - "renew.*access.*token"
---

# OAuth2 Token Refresh Implementation

## Overview

OAuth2 uses two types of tokens:
- **Access Token**: Short-lived (15 min), used to call APIs
- **Refresh Token**: Long-lived (7 days), used to get new access tokens without re-authentication

When access token expires, the client automatically uses the refresh token to get a new access token.

## Architecture

```
┌─────────────┐
│ Client App  │
└──────┬──────┘
       │ 1. Access Token Expired (401)
       ↓
┌─────────────────────────────────────┐
│ Refresh Token Handler               │
│ (auto_refresh_on_401 middleware)    │
└──────┬────────────────────────────────┘
       │ 2. Send Refresh Token
       ↓
┌────────────────────┐
│ Authorization      │
│ Server /refresh    │
└──────┬─────────────┘
       │ 3. Return New Access Token
       ↓
┌─────────────────────────────────────┐
│ Store New Access Token              │
│ (secure cookie / storage)           │
└──────┬────────────────────────────────┘
       │ 4. Retry Original Request
       ↓
┌──────────────────────────────────┐
│ Protected Resource (success!)     │
└──────────────────────────────────┘
```

## Client Implementation

### Store Tokens Securely

```python
# client-app/auth.py
from flask import session, current_app
from datetime import datetime

def store_tokens(token_response: dict):
    """
    Store tokens in secure session after OAuth2 exchange.
    
    Args:
        token_response: Response from /token endpoint
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 900,  # 15 minutes
                "token_type": "Bearer"
            }
    """
    session['access_token'] = token_response['access_token']
    session['refresh_token'] = token_response['refresh_token']
    
    # Store expiry time
    expires_in = token_response.get('expires_in', 900)
    session['token_expires_at'] = datetime.utcnow().timestamp() + expires_in
    
    session.permanent = True  # Make session persistent
    current_app.permanent_session_lifetime = timedelta(days=7)

def get_access_token() -> str:
    """Get current access token, refreshing if needed."""
    access_token = session.get('access_token')
    expires_at = session.get('token_expires_at')
    
    if not access_token or not expires_at:
        return None
    
    # If expired or expiring soon (< 60 sec), refresh
    if datetime.utcnow().timestamp() > expires_at - 60:
        refresh_token(session['refresh_token'])
        access_token = session.get('access_token')
    
    return access_token
```

### Refresh Token Endpoint Handler

```python
# client-app/auth.py
import requests
from flask import session, redirect, url_for

def refresh_token(refresh_token_value: str) -> bool:
    """
    Exchange refresh token for new access token.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            f"{OAUTH2_TOKEN_URL}",
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token_value,
                'client_id': OAUTH2_CLIENT_ID,
                'client_secret': OAUTH2_CLIENT_SECRET
            },
            timeout=5
        )
        
        if response.status_code == 200:
            token_response = response.json()
            store_tokens(token_response)
            return True
        else:
            # Refresh token invalid or expired - need re-authentication
            clear_session()
            return False
            
    except requests.RequestException as e:
        current_app.logger.error(f"Token refresh failed: {e}")
        return False

def clear_session():
    """Clear all session tokens."""
    session.clear()
```

### Automatic Refresh with HTTP Interceptor

```python
# client-app/api_client.py
import requests
from functools import wraps
from auth import get_access_token, refresh_token, clear_session

class OAuth2Session(requests.Session):
    """HTTP session with automatic token refresh."""
    
    def request(self, method, url, **kwargs):
        """Override request to handle token refresh on 401."""
        
        # Set Authorization header
        token = get_access_token()
        if token:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = f'Bearer {token}'
        
        # Make request
        response = super().request(method, url, **kwargs)
        
        # If 401, try refreshing token and retry once
        if response.status_code == 401:
            current_app.logger.info(f"401 received, attempting token refresh")
            
            refresh_token_value = session.get('refresh_token')
            if refresh_token_value and refresh_token(refresh_token_value):
                # Retry with new token
                token = get_access_token()
                kwargs['headers']['Authorization'] = f'Bearer {token}'
                response = super().request(method, url, **kwargs)
            else:
                # Refresh failed - clear session and require re-login
                clear_session()
        
        return response

# Usage
oauth2_session = OAuth2Session()
profile = oauth2_session.get(f"{RESOURCE_SERVER_URL}/api/user/profile")
```

### Flask View with Token Refresh

```python
# client-app/routes.py
from flask import render_template, redirect, url_for
from auth import get_access_token, clear_session
from api_client import oauth2_session

@app.route('/profile')
def profile():
    """Display user profile - with automatic token refresh."""
    
    try:
        # This will auto-refresh if needed
        response = oauth2_session.get(
            f"{RESOURCE_SERVER_URL}/api/user/profile"
        )
        
        if response.status_code == 200:
            user_profile = response.json()
            return render_template('profile.html', user=user_profile)
        else:
            # Token issues - force re-login
            clear_session()
            return redirect(url_for('login'))
            
    except Exception as e:
        app.logger.error(f"Error fetching profile: {e}")
        return render_template('error.html', error="Could not load profile"), 500
```

## Authorization Server Implementation

### Add Refresh Endpoint

```python
# auth-server/routes.py
from fastapi import APIRouter, HTTPException, Form
from security import (
    validate_refresh_token,
    generate_access_token,
    update_token
)

router = APIRouter()

@router.post("/token")
async def token_endpoint(
    grant_type: str = Form(...),
    code: str = Form(None),
    refresh_token: str = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(None),
    code_verifier: str = Form(None)  # PKCE
):
    """
    Token endpoint supporting multiple grant types.
    
    Supports:
    - authorization_code: Exchange auth code for tokens
    - refresh_token: Exchange refresh token for new access token
    """
    
    # Validate client credentials first
    client = validate_client(client_id, client_secret)
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials"
        )
    
    if grant_type == "authorization_code":
        return handle_authorization_code(
            code, redirect_uri, client, code_verifier
        )
    
    elif grant_type == "refresh_token":
        return handle_refresh_token(refresh_token, client)
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported grant type: {grant_type}"
        )

def handle_refresh_token(refresh_token_value: str, client):
    """Handle refresh_token grant type."""
    
    # Validate refresh token
    token_record = validate_refresh_token(refresh_token_value)
    if not token_record or token_record.client_id != client.client_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    user = token_record.user
    
    # Generate new access token
    access_token = generate_access_token(
        user_id=user.id,
        client_id=client.client_id,
        scopes=token_record.scopes
    )
    
    # Create new refresh token (optional - can reuse)
    new_refresh_token = generate_refresh_token(
        user_id=user.id,
        client_id=client.client_id
    )
    
    # Update database record
    update_token(token_record, access_token, new_refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in": 900  # 15 minutes
    }
```

### Token Model and Validation

```python
# auth-server/models.py
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from datetime import datetime, timedelta

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True)
    token_hash = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(String, ForeignKey("oauth_client.client_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Typically 7 days
    revoked = Column(Boolean, default=False)
    
    scopes = Column(String)  # Space-separated scopes
    
    user = relationship("User", back_populates="refresh_tokens")
    client = relationship("OAuthClient")
    
    @property
    def is_valid(self) -> bool:
        """Check if refresh token is still valid."""
        return (
            not self.revoked and 
            datetime.utcnow() < self.expires_at
        )

# auth-server/security.py
import secrets
import hashlib

def generate_refresh_token_value() -> str:
    """Generate cryptographically secure refresh token."""
    return secrets.token_urlsafe(48)

def hash_token(token: str) -> str:
    """Hash token for storage (don't store plaintext)."""
    return hashlib.sha256(token.encode()).hexdigest()

def validate_refresh_token(token_value: str):
    """Validate refresh token and return if valid."""
    token_hash = hash_token(token_value)
    
    token_record = db.query(RefreshToken).filter_by(
        token_hash=token_hash
    ).first()
    
    if not token_record or not token_record.is_valid:
        return None
    
    return token_record

def revoke_refresh_token(token_value: str):
    """Revoke a refresh token (logout)."""
    token_hash = hash_token(token_value)
    token_record = db.query(RefreshToken).filter_by(
        token_hash=token_hash
    ).first()
    
    if token_record:
        token_record.revoked = True
        db.commit()
```

## Refresh Token Security Best Practices

### 1. Store Refresh Tokens Securely

```python
# ✅ GOOD: HttpOnly, Secure cookies
response.set_cookie(
    'refresh_token',
    refresh_token,
    httponly=True,       # Cannot be accessed by JavaScript
    secure=True,         # Only sent over HTTPS
    samesite='Strict',   # CSRF protection
    max_age=7*24*60*60   # 7 days
)

# ❌ BAD: Exposed in localStorage
# localStorage.setItem('refresh_token', token)  # Can be stolen by XSS!
```

### 2. Rotate Refresh Tokens

```python
def handle_refresh_token(refresh_token_value: str, client):
    """Refresh token - issue new refresh token."""
    
    # Validate old token
    token_record = validate_refresh_token(refresh_token_value)
    if not token_record:
        raise HTTPException(status_code=401)
    
    # Generate NEW refresh token (rotation)
    new_refresh_token = generate_refresh_token_value()
    
    # Revoke old token
    token_record.revoked = True
    
    # Create new token record
    new_token_record = RefreshToken(
        token_hash=hash_token(new_refresh_token),
        user_id=token_record.user_id,
        client_id=client.client_id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        scopes=token_record.scopes
    )
    db.add(new_token_record)
    db.commit()
    
    # Return new tokens
    return {
        "access_token": generate_access_token(...),
        "refresh_token": new_refresh_token,  # NEW token
        "expires_in": 900
    }
```

### 3. Implement Refresh Token Families

Detect token reuse attacks:

```python
# auth-server/models.py
class RefreshToken(Base):
    family_id = Column(String, index=True)  # All related tokens share ID

# auth-server/security.py
def handle_refresh_token(token_value: str, client):
    """Detect token family for detecting reuse attacks."""
    
    token_record = validate_refresh_token(token_value)
    if not token_record:
        raise HTTPException(status_code=401)
    
    # Check for token reuse in family
    reused = db.query(RefreshToken).filter(
        RefreshToken.family_id == token_record.family_id,
        RefreshToken.created_at > token_record.created_at,
        RefreshToken.revoked == False
    ).first()
    
    if reused:
        # Token reuse detected - revoke entire family!
        revoke_family(token_record.family_id)
        raise HTTPException(
            status_code=401,
            detail="Token reuse detected - session terminated"
        )
    
    # Issue new token with same family_id
    new_token = generate_refresh_token_value()
    new_record = RefreshToken(
        family_id=token_record.family_id,  # Same family
        token_hash=hash_token(new_token),
        ...
    )
    db.add(new_record)
    token_record.revoked = True
    db.commit()
    
    return {"access_token": ..., "refresh_token": new_token}
```

## Testing Token Refresh

```python
# tests/test_token_refresh.py
import pytest
from auth_client import get_tokens, refresh_tokens

def test_refresh_token_success():
    """Test successful token refresh."""
    tokens = get_tokens(username="alice", password="alice123")
    
    # Wait for access token to expire (or mock time)
    new_tokens = refresh_tokens(tokens['refresh_token'])
    
    assert new_tokens['access_token'] != tokens['access_token']
    assert 'refresh_token' in new_tokens
    assert new_tokens['token_type'] == 'Bearer'

def test_refresh_invalid_token():
    """Test refresh with invalid token."""
    with pytest.raises(Exception):
        refresh_tokens("invalid-token")

def test_refresh_expired_token():
    """Test refresh with expired refresh token."""
    # Manually expire token in DB
    # Then try to refresh
    with pytest.raises(Exception):
        refresh_tokens(expired_token)

def test_token_reuse_detection():
    """Test that reusing a refresh token is detected."""
    tokens = get_tokens(username="alice", password="alice123")
    old_token = tokens['refresh_token']
    
    # First refresh - succeeds
    new_tokens_1 = refresh_tokens(old_token)
    
    # Try to reuse old token - should fail
    with pytest.raises(Exception) as exc:
        refresh_tokens(old_token)
    
    assert "reuse" in str(exc.value).lower()
```

## Handling Logout

```python
# auth-server/routes.py
@router.post("/logout")
async def logout(request: Request):
    """
    Logout - revoke all tokens for user.
    
    Required: Authorization: Bearer <access_token>
    """
    user = await get_current_user(request)
    
    # Revoke all refresh tokens
    revoke_user_refresh_tokens(user.id)
    
    return {"message": "Logged out successfully"}

# auth-server/security.py
def revoke_user_refresh_tokens(user_id: int):
    """Revoke all refresh tokens for a user."""
    db.query(RefreshToken).filter_by(
        user_id=user_id
    ).update({"revoked": True})
    db.commit()
```

## Monitoring & Debugging

```python
# View refresh token usage
docker-compose exec postgres psql -U oauth2_user -d oauth2

SELECT user_id, client_id, created_at, revoked
FROM refresh_tokens
ORDER BY created_at DESC
LIMIT 20;

# View suspicious patterns
SELECT user_id, COUNT(*) as refresh_count
FROM refresh_tokens
WHERE created_at > now() - interval '1 hour'
GROUP BY user_id
ORDER BY refresh_count DESC;
```

---

For more details, see [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md)
