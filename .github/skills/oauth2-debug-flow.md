---
name: "oauth2-debug-flow"
description: "Debug and troubleshoot OAuth2 authorization code flow, token exchange, and token validation"
patterns:
  - "debug.*oauth"
  - "oauth.*not working"
  - "token.*error"
  - "authorization.*failed"
---

# Debugging OAuth2 Flow Issues

## Common Issues & Solutions

### Issue 1: "Invalid Client Credentials"

**Symptoms**: 401 error when exchanging auth code for token

**Root Causes**:
1. Client ID mismatch
2. Client Secret incorrect
3. Client not registered in Authorization Server
4. Redirect URI mismatch

**Debug Steps**:
```bash
# 1. Check environment variables
grep OAUTH2_CLIENT_ID .env
grep OAUTH2_CLIENT_SECRET .env

# 2. Verify registered client in database
docker-compose exec auth-server python
# In Python shell:
from models import OAuthClient
from database import SessionLocal
db = SessionLocal()
client = db.query(OAuthClient).filter_by(client_id="web-client").first()
print(f"Client ID: {client.client_id}")
print(f"Secret match: {client.secret == 'web-client-secret'}")
print(f"Redirect URIs: {client.redirect_uris}")

# 3. Check logs
make logs-auth | grep "invalid_client\|client credentials"
```

**Solution**:
```bash
# Re-seed database with correct credentials
make seed

# Or manually update:
docker-compose exec postgres psql -U oauth2_user -d oauth2
# SQL: UPDATE oauth_client SET secret='new-secret' WHERE client_id='web-client';
```

### Issue 2: "Invalid Redirect URI"

**Symptoms**: Authorization request rejected at auth server

**Root Causes**:
1. Redirect URI in .env doesn't match registered URI
2. HTTP vs HTTPS mismatch
3. Port number mismatch
4. Path typo (e.g., `/callback` vs `/callbakc`)

**Debug Steps**:
```bash
# 1. Check Client App's redirect URI setting
grep OAUTH2_REDIRECT_URI .env
# Should be: http://localhost:5001/callback

# 2. Verify it's registered on Authorization Server
docker-compose exec auth-server python
from models import OAuthClient
from database import SessionLocal
db = SessionLocal()
client = db.query(OAuthClient).filter_by(client_id="web-client").first()
print("Allowed redirect URIs:")
for uri in client.redirect_uris:
    print(f"  - {uri}")

# 3. Check callback route exists in Client App
grep -n "def.*callback" client-app/routes.py
```

**Solution**:
```bash
# Update .env to match registered URI
echo "OAUTH2_REDIRECT_URI=http://localhost:5001/callback" >> .env

# Or update database
docker-compose exec postgres psql -U oauth2_user -d oauth2
# SQL: UPDATE oauth_client SET redirect_uris='http://localhost:5001/callback' WHERE client_id='web-client';

# Restart services
make down && make up
```

### Issue 3: "Authorization Code Invalid/Expired"

**Symptoms**: Auth code exchange fails even immediately after user approval

**Root Causes**:
1. Auth code already used
2. Auth code expired (default 10 minutes)
3. PKCE challenge mismatch
4. State parameter mismatch

**Debug Steps**:
```bash
# 1. Check auth code expiration setting
grep AUTHORIZATION_CODE_EXPIRE_MINUTES .env

# 2. View auth server logs
make logs-auth | grep -i "authorization_code\|pkce\|state"

# 3. Test with fresh auth code
# Clear browser cookies
# Reload http://localhost:5001
# Click login
# Check logs for issued auth code

# 4. Check PKCE implementation
grep -n "code_verifier\|code_challenge" client-app/auth.py
```

**Solution**:
```bash
# Increase auth code expiration (if needed)
echo "AUTHORIZATION_CODE_EXPIRE_MINUTES=30" >> .env
make down && make up

# Or verify PKCE is implemented correctly in client app
# See section "PKCE Verification" below
```

### Issue 4: "Token Has Expired"

**Symptoms**: 401 error when calling Resource Server API after 15 minutes

**Root Cause**:
- Access token expires after 15 minutes by design

**Expected Behavior**:
- Client App should automatically use refresh token to get new access token

**Debug Steps**:
```bash
# 1. Check token expiry settings
grep "ACCESS_TOKEN_EXPIRE\|REFRESH_TOKEN_EXPIRE" .env

# 2. Verify refresh logic in Client App
grep -A 10 "def refresh_token\|refresh_access_token" client-app/auth.py

# 3. Check if refresh token is stored
docker-compose exec client-app python -c "
from flask import session
print('Stored refresh token:', session.get('refresh_token'))
"

# 4. View auth server refresh endpoint logs
make logs-auth | grep "refresh\|token"
```

**Solution**:
```bash
# For development, increase access token expiry (NOT for production!)
echo "ACCESS_TOKEN_EXPIRE_MINUTES=480" >> .env  # 8 hours
make down && make up

# Or ensure refresh logic is working:
# Check client-app/auth.py has refresh_token() function
```

### Issue 5: "Unauthorized" at Resource Server

**Symptoms**: 401 error when calling `/api/user/profile` with token

**Root Causes**:
1. Token not in Authorization header
2. Token invalid/tampered
3. Token signature verification failed
4. Token validation mode misconfigured

**Debug Steps**:
```bash
# 1. Check token is being sent
make logs-resource | grep -i "authorization\|bearer"

# 2. Verify token format
# In browser console or test:
const token = localStorage.getItem('access_token');
console.log('Token header:', token.split('.')[0]);  // Should be JWT header

# 3. Check token validation mode
grep TOKEN_VALIDATION_MODE .env

# 4. Verify shared secret between servers
grep "SECRET_KEY" .env  # Should be same for all services

# 5. Decode token and check expiry
python3 -c "
import jwt
token = 'eyJ...'
decoded = jwt.decode(token, options={'verify_signature': False})
import json
print(json.dumps(decoded, indent=2))
"
```

**Solution**:
```bash
# Ensure Authorization header is sent
# In client app or curl:
curl -H "Authorization: Bearer $TOKEN" http://localhost:5002/api/user/profile

# Verify token validation mode
echo "TOKEN_VALIDATION_MODE=jwt" >> .env
make logs-resource

# Ensure shared secret
grep AUTH_SERVER_SECRET_KEY .env
# Should be consistent across services

# Test token validation
curl -X POST http://localhost:5000/introspect \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=$TOKEN"
```

## PKCE Verification

PKCE (Proof Key for Code Exchange) prevents authorization code interception:

```bash
# 1. Verify PKCE is implemented in Client App
grep -n "code_verifier\|code_challenge\|S256" client-app/auth.py

# 2. Check PKCE parameters in auth request
make logs-auth | grep "code_challenge"

# 3. Verify code_verifier is sent in token request
make logs-auth | grep "code_verifier"

# 4. Test PKCE manually
python3 << 'EOF'
import hashlib
import base64
import os

# Generate code verifier (43-128 chars)
code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
print(f"Code Verifier: {code_verifier}")

# Generate code challenge (S256)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')
print(f"Code Challenge: {code_challenge}")
EOF
```

## State Parameter Verification

State parameter prevents CSRF attacks:

```bash
# 1. Check state is generated
make logs-auth | grep "state="

# 2. Verify state is validated in callback
grep -n "state" client-app/routes.py

# 3. Check state is stored in session
grep -n "session\['state'\]" client-app/auth.py
```

## Token Validation Flow

### JWT Mode (Default)
```
1. Client sends token: Authorization: Bearer eyJhbGc...
   ↓
2. Resource Server extracts token
   ↓
3. Validates JWT signature using AUTH_SERVER_SECRET_KEY
   ↓
4. Checks token expiry, scopes, user
   ↓
5. Returns 200 if valid, 401 if invalid
```

### Introspection Mode
```
1. Client sends token: Authorization: Bearer eyJhbGc...
   ↓
2. Resource Server calls: POST /introspect on Auth Server
   ↓
3. Auth Server verifies token, returns {active: true, ...}
   ↓
4. Resource Server grants access if active=true
```

**To test introspection endpoint**:
```bash
# Get a valid token from auth server
TOKEN=$(curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=web-client&client_secret=web-client-secret" \
  | jq -r '.access_token')

# Check token on auth server
curl -X POST http://localhost:5000/introspect \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=$TOKEN" | jq .
```

## End-to-End Flow Test

```bash
# 1. Start services
make up && make seed

# 2. Get access token
TOKEN=$(curl -s -X POST http://localhost:5000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=alice&password=alice123&client_id=web-client&client_secret=web-client-secret" \
  | jq -r '.access_token')

echo "Access Token: $TOKEN"

# 3. Call Resource Server with token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5002/api/user/profile | jq .

# 4. Try with invalid token
curl -H "Authorization: Bearer invalid-token" \
  http://localhost:5002/api/user/profile

# 5. Try without token
curl http://localhost:5002/api/user/profile
```

## Viewing Raw Requests/Responses

### Using curl with verbose
```bash
curl -v -H "Authorization: Bearer $TOKEN" \
  http://localhost:5002/api/user/profile
```

### Using tcpdump to inspect traffic
```bash
# Monitor traffic between resource-server and auth-server
docker-compose exec resource-server tcpdump -i any -A "host auth-server"
```

### Check logs in detail
```bash
# Enable debug logging
echo "DEBUG=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
make down && make up

# View logs
make logs | grep -i "token\|auth\|oauth"
```

## Testing with Postman/Insomnia

1. **Get Authorization Code**
   ```
   GET http://localhost:5000/authorize?
     response_type=code&
     client_id=web-client&
     redirect_uri=http://localhost:5001/callback&
     state=abc123&
     scope=user:read
   ```

2. **Exchange Code for Token**
   ```
   POST http://localhost:5000/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&
   code=AUTH_CODE_HERE&
   client_id=web-client&
   client_secret=web-client-secret&
   redirect_uri=http://localhost:5001/callback
   ```

3. **Call Protected Resource**
   ```
   GET http://localhost:5002/api/user/profile
   Authorization: Bearer ACCESS_TOKEN_HERE
   ```

## Performance Debugging

```bash
# Check response times
curl -w "Time: %{time_total}s\n" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5002/api/user/profile

# Monitor database queries
make logs | grep "SELECT\|INSERT\|UPDATE"

# Check container resource usage
docker stats
```

## Reset Everything

When stuck, reset to clean state:

```bash
# Nuclear option
make clean-all

# Start fresh
make up
make migrate
make seed

# Test basic flow
make test-e2e
```

---

Still having issues? Check [AGENTS.md](AGENTS.md#troubleshooting) or create an issue with:
- Error message
- Service logs (`make logs`)
- `.env` configuration (redact secrets)
