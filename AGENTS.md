# OAuth2 Implementation - Agent Customization Guide

## Project Overview

This is a **practical OAuth2 implementation** demonstrating two OAuth2 flows with three main components:

1. **Authorization Server** - Issues tokens for both Authorization Code and Client Credentials flows
2. **Resource Server** - Protects user APIs and machine APIs using OAuth2 tokens
3. **Client Application** - Browser web app demonstrating the Authorization Code flow

A CLI script (`scripts/service_client.py`) demonstrates the Client Credentials flow without a web server.

All components are containerized with Docker Compose for local and cloud execution.

## Flows at a Glance

| | Authorization Code | Client Credentials |
|---|---|---|
| Who | Human user | Machine / service |
| Browser redirect | Yes | No |
| PKCE + State | Yes | No |
| Refresh token | Yes | No |
| Token `sub` | User ID | Client ID |
| Demo component | `client-app/` | `scripts/service_client.py` |

## Architecture & Components

### Authorization Server (`/auth-server`)
- **Tech**: Python FastAPI
- **Responsibility**: OAuth2 token issuance for both grant types, user authentication, token validation
- **Key Endpoints**:
  - `GET /authorize` - Initiates Authorization Code flow (redirects user to login)
  - `POST /token` - Token endpoint; handles both `authorization_code` and `client_credentials` grant types
  - `POST /refresh` - Refresh token endpoint (Authorization Code flow only)
  - `GET /userinfo` - Returns user profile (requires user token)
  - `POST /introspect` - Token introspection (works for both token types)
  - `GET /.well-known/oauth-metadata` - OpenID Connect metadata
- **Database**: SQLite (local) or PostgreSQL (cloud)
- **Key Files**:
  - `models.py` - Database models (User, OAuthClient with `allowed_grant_types`, Token, AuthorizationCode)
  - `security.py` - Token generation (`create_user_token`, `create_client_token`), JWT validation
  - `routes.py` - OAuth2 endpoints; `/token` branches on `grant_type`

### Resource Server (`/resource-server`)
- **Tech**: Python FastAPI
- **Responsibility**: Protect APIs, validate OAuth2 tokens, return resources
- **Key Endpoints**:
  - `GET /api/user/profile` - Requires user Bearer token (`@require_oauth2`)
  - `GET /api/user/data` - Requires user Bearer token (`@require_oauth2`)
  - `GET /api/service/stats` - Requires machine Bearer token (`@require_client_token`)
  - `GET /health` - Health check
- **Token Validation**: Validates JWT locally or via Auth Server introspection (set by `TOKEN_VALIDATION_MODE`)
- **Key Files**:
  - `security.py` - Two decorators: `@require_oauth2` (populates `request.oauth2_user`) and `@require_client_token` (populates `request.oauth2_client`); both share the same JWT validation path
  - `routes.py` - User endpoints and machine endpoints
  - `config.py` - Authorization Server URL configuration

### Client Application (`/client-app`)
- **Tech**: Python Flask with Web UI
- **Responsibility**: Demonstrates the Authorization Code flow with a browser UI
- **Key Flows**:
  1. Redirect user to Authorization Server (`/authorize` with PKCE + state)
  2. Receive authorization code at `/callback`
  3. Exchange code for access token (server-side, never exposed to browser)
  4. Use access token to call Resource Server user APIs
  5. Handle token refresh when needed
- **Session Management**: Secure session cookies with token storage
- **Key Files**:
  - `auth.py` - OAuth2 flow handling (PKCE generation, state validation, code exchange)
  - `routes.py` - Web routes and callback handler
  - `config.py` - OAuth2 credentials and URLs

### Service Client (`scripts/service_client.py`)
- **Tech**: Plain Python script (~40 lines), no web server
- **Responsibility**: Demonstrates the Client Credentials flow end-to-end
- **Flow**:
  1. POST `client_id` + `client_secret` to `/token` with `grant_type=client_credentials`
  2. Print the decoded token claims (shows `sub` = client ID, no user)
  3. Call `/api/service/stats` with the token
  4. Print the response
- Run with `python scripts/service_client.py` or `make demo-cc`

### Resource Owner
- A user with credentials (username/password) stored in Authorization Server
- Participates only in the Authorization Code flow (not Client Credentials)
- Logs in at Authorization Server to authorize Client Application
- No direct authentication with Resource Server (only token-based)

## Development Commands

### Local Setup
```bash
# Install dependencies
make install

# Create environment files
make setup-env

# Start all services with Docker Compose
make up

# Run database migrations
make migrate
```

### Testing
```bash
# Run all tests
make test

# Run specific component tests
make test-auth-server
make test-resource-server
make test-client-app

# Test OAuth2 flows end-to-end
make test-e2e      # Authorization Code flow (browser-based)
make test-e2e-cc   # Client Credentials flow (machine-to-machine)

# Generate coverage report
make coverage
```

### Development
```bash
# Start services with hot-reload
make dev

# View logs from all services
make logs

# Stop all services
make down

# Clean up volumes and containers
make clean
```

### URLs (Local Development)
- **Client Application**: http://localhost:5001
- **Authorization Server**: http://localhost:5000
- **Resource Server**: http://localhost:5002
- **Resource Server API**: http://localhost:5002/api

## Key Conventions & Patterns

### Token Handling
- **Access Token**: JWT with short expiry (15 minutes), included as `Authorization: Bearer <token>` header
- **Refresh Token**: Opaque token with long expiry (7 days), stored in secure cookies (HttpOnly, Secure)
- **Token Validation**: Authorization Server validates JWT signature or calls introspection endpoint

### Security Best Practices
- **HTTPS/TLS**: Always required in production (local uses HTTP for development)
- **PKCE** (Proof Key for Code Exchange): Implemented for all flows to prevent authorization code interception
- **State Parameter**: Used to prevent CSRF attacks during redirects
- **Secure Cookies**: HttpOnly, Secure flags enabled for refresh tokens
- **CORS**: Configured to allow cross-origin requests only between known services

### Configuration
- Environment-specific config via `.env` files (not committed to git)
- Separate configs for local development, testing, and cloud deployment
- Database connection strings, OAuth2 credentials, and secret keys in environment variables

### Database
- **Models**: Standardized ORM models (SQLAlchemy) across all components
- **Migrations**: Alembic-based migrations in `/migrations`
- **Seeding**: Development database seeded with test users and clients via `scripts/seed.py`

### Logging & Debugging
- Structured logging (JSON format) for easier parsing in cloud environments
- Debug endpoints disabled in production
- Request/response logging for OAuth2 endpoints includes token grant type (not secrets)

## Docker Compose Setup

### Services
1. **auth-server**: Port 5000, depends on postgres
2. **resource-server**: Port 5002, depends on auth-server
3. **client-app**: Port 5001, depends on auth-server
4. **postgres**: Port 5432, volume-persisted database

### Volumes
- `postgres_data`: PostgreSQL database persistence
- `.env` files: Configuration mounted at service startup

### Network
- Custom bridge network `oauth2-network` for service-to-service communication
- All services communicate via service names (e.g., `http://auth-server:5000`)

## Common Development Tasks

### Adding a New Protected Endpoint (Resource Server)
1. Define route in `resource_server/routes.py`
2. Add `@require_oauth2` decorator for token validation
3. Access user info via `request.oauth2_user` context
4. Test with Bearer token from Authorization Server

### Adding a New Grant Type
1. Add a `create_<type>_token()` function in `auth_server/security.py`
2. Add a branch in the `/token` route in `auth_server/routes.py` keyed on `grant_type`
3. Register the grant type in `OAuthClient.allowed_grant_types` and update `scripts/seed.py`
4. Add a client demo (web app or script) that exercises the new flow
5. Add tests in `tests/auth_server/test_token_<type>.py`

### Debugging OAuth2 Flows
1. Enable debug mode: Set `DEBUG=true` in `.env`
2. Check logs: `make logs` and filter by service
3. Use browser dev tools to inspect Authorization header
4. Token introspection endpoint: `POST /auth-server/introspect` with token

## File Structure Reference

```
OAuth2/
├── auth-server/              # Authorization Server (FastAPI) — both grant types
│   ├── models.py            # User, OAuthClient (with allowed_grant_types), Token, AuthorizationCode
│   ├── security.py          # create_user_token(), create_client_token(), validate_token()
│   ├── routes.py            # /token branches on grant_type; /authorize for auth code only
│   ├── config.py
│   └── requirements.txt
├── resource-server/          # Resource Server (FastAPI) — user and machine APIs
│   ├── security.py          # @require_oauth2 (user tokens), @require_client_token (machine tokens)
│   ├── routes.py            # /api/user/* and /api/service/*
│   ├── config.py
│   └── requirements.txt
├── client-app/               # Client Web App (Flask) — Authorization Code flow demo
│   ├── auth.py              # PKCE generation, state param, code exchange, token refresh
│   ├── routes.py
│   ├── config.py
│   └── requirements.txt
├── migrations/               # Database migrations (Alembic)
├── tests/
│   ├── auth_server/         # Unit tests for both grant types
│   ├── resource_server/     # Tests for user and machine endpoints
│   └── e2e/                 # test_auth_code_flow.py, test_client_credentials_flow.py
├── scripts/
│   ├── seed.py              # Seeds users + registers web-client and service-client
│   └── service_client.py   # Client Credentials flow demo (~40 lines)
├── docker-compose.yml        # Docker Compose configuration
├── Makefile                  # Development commands (includes demo-cc, test-e2e-cc)
└── .env.example              # Environment template
```

## Related Documentation

- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749) - Authorization Framework
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636) - Proof Key for Code Exchange
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html) - Identity Layer
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - FastAPI docs
- [Flask-OAuthlib](https://flask-oauthlib.readthedocs.io/) - Flask OAuth support

## Troubleshooting

### "Invalid client credentials" error
- Verify Client ID and Secret match in Authorization Server database
- Check `.env` variables for typos

### "Token has expired" error
- Token expiry (15 min) exceeded; use refresh token to get new access token
- Check system clock synchronization if JWT validation fails

### Services can't communicate
- Verify `docker-compose up` completed without errors
- Check service names in `config.py` match docker-compose service names
- Use `docker network inspect oauth2-network` to debug connectivity

### Database migration issues
- Run `make migrate` to initialize schema
- Clear database: `make clean` then `make up`
