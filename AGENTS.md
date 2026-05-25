# OAuth2 Implementation - Agent Customization Guide

## Project Overview

This is a **practical OAuth2 implementation** demonstrating the complete OAuth2 authorization code flow with three main components:

1. **Authorization Server** - Issues access tokens and refresh tokens
2. **Resource Server** - Protects API endpoints using OAuth2 tokens
3. **Client Application** - Requests access on behalf of Resource Owner

All components are containerized with Docker Compose for local and cloud execution.

## Architecture & Components

### Authorization Server (`/auth-server`)
- **Tech**: Python FastAPI
- **Responsibility**: OAuth2 token issuance, user authentication, token validation
- **Key Endpoints**:
  - `POST /authorize` - Authorization endpoint (initiates OAuth2 flow)
  - `POST /token` - Token endpoint (exchanges auth code for access token)
  - `POST /refresh` - Refresh token endpoint
  - `GET /.well-known/oauth-metadata` - OpenID Connect metadata
- **Database**: SQLite (local) or PostgreSQL (cloud)
- **Key Files**:
  - `models.py` - Database models (User, Client, Token, AuthorizationCode)
  - `security.py` - Token generation, validation, JWT handling
  - `routes.py` - OAuth2 endpoints

### Resource Server (`/resource-server`)
- **Tech**: Python FastAPI
- **Responsibility**: Protect APIs, validate OAuth2 tokens, return resources
- **Key Endpoints**:
  - `GET /api/user/profile` - Protected endpoint requiring Bearer token
  - `GET /api/user/data` - Protected resource
  - `GET /api/resource-server/health` - Health check
- **Token Validation**: Calls Authorization Server's token introspection or validates JWT locally
- **Key Files**:
  - `security.py` - Token validation middleware
  - `routes.py` - Protected resource endpoints
  - `config.py` - Authorization Server URL configuration

### Client Application (`/client-app`)
- **Tech**: Python Flask with Web UI
- **Responsibility**: Initiates OAuth2 flow, stores user credentials, calls Resource Server
- **Key Flows**:
  1. Redirect user to Authorization Server
  2. Receive authorization code
  3. Exchange code for access token
  4. Use access token to call Resource Server
  5. Handle token refresh when needed
- **Session Management**: Secure session cookies with token storage
- **Key Files**:
  - `auth.py` - OAuth2 flow handling
  - `routes.py` - Web routes and callbacks
  - `config.py` - OAuth2 credentials and URLs

### Resource Owner
- A user with credentials (username/password) stored in Authorization Server
- User logs in at Authorization Server to authorize Client Application
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

# Test OAuth2 flow end-to-end
make test-e2e

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

### Implementing New Authorization Grant Type
1. Add logic in `auth_server/security.py` for token generation
2. Add endpoint in `auth_server/routes.py`
3. Update client `auth.py` to support new flow
4. Add tests in `tests/` directory

### Debugging OAuth2 Flows
1. Enable debug mode: Set `DEBUG=true` in `.env`
2. Check logs: `make logs` and filter by service
3. Use browser dev tools to inspect Authorization header
4. Token introspection endpoint: `POST /auth-server/introspect` with token

## File Structure Reference

```
OAuth2/
├── auth-server/              # Authorization Server (FastAPI)
│   ├── models.py
│   ├── security.py          # Token generation & validation
│   ├── routes.py
│   ├── config.py
│   └── requirements.txt
├── resource-server/          # Resource Server (FastAPI)
│   ├── security.py          # Token validation middleware
│   ├── routes.py
│   ├── config.py
│   └── requirements.txt
├── client-app/               # Client Web App (Flask)
│   ├── auth.py              # OAuth2 flow
│   ├── routes.py
│   ├── config.py
│   └── requirements.txt
├── migrations/               # Database migrations (Alembic)
├── tests/                    # Test suite
├── scripts/                  # Utility scripts (seed.py, etc.)
├── docker-compose.yml        # Docker Compose configuration
├── Makefile                  # Development commands
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
