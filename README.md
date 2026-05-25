# OAuth2 Implementation - Authorization Code Flow & Client Credentials Flow

A **practical, educational, and production-ready** implementation of two OAuth2 flows — Authorization Code (user-facing) and Client Credentials (machine-to-machine) — with three services running in Docker containers.

## 📋 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local development)
- Make (optional, for convenient commands)

### 1-Minute Setup

```bash
# Create environment file
make setup-env

# Start all services (PostgreSQL, Auth Server, Resource Server, Client App)
make up

# Open in browser
open http://localhost:5001
```

## 🔄 OAuth2 Flows

This project demonstrates two complete OAuth2 flows. Understanding when to use each is the core learning goal.

### Flow 1: Authorization Code (user-facing)

Used when a **human user** grants a third-party app access to their data.

```
1. User visits Client App
   ↓
2. Client redirects user to Authorization Server (/authorize)
   ↓
3. User logs in with username/password at Authorization Server
   ↓
4. Authorization Server asks "Allow client-app to access your data?"
   ↓
5. User approves → Authorization Server redirects to Client with AUTH CODE
   ↓
6. Client App exchanges AUTH CODE for ACCESS TOKEN (backend, secure)
   ↓
7. Client uses ACCESS TOKEN to call Resource Server APIs
   ↓
8. Resource Server validates token and returns protected resources
   ↓
9. When token expires, Client uses REFRESH TOKEN to get new ACCESS TOKEN
```

### Flow 2: Client Credentials (machine-to-machine)

Used when a **service or background job** accesses an API with no user involved.

```
1. Service POSTs client_id + client_secret to Authorization Server (/token)
   ↓
2. Authorization Server validates credentials and issues ACCESS TOKEN
   (no redirect, no user login, no PKCE — just a credential check)
   ↓
3. Service uses ACCESS TOKEN to call Resource Server machine APIs
   ↓
4. Resource Server validates token and returns data
   ↓
5. When token expires, Service requests a new one (no refresh token needed)
```

### When to use which flow

| | Authorization Code | Client Credentials |
|---|---|---|
| **Who authenticates** | A human user | A machine / service |
| **Involves a browser** | Yes | No |
| **User consent screen** | Yes | No |
| **PKCE + State param** | Yes (required) | No |
| **Refresh token issued** | Yes | No (re-request instead) |
| **Token `sub` claim** | User ID | Client ID |
| **Example use case** | "Login with Google" | Microservice API call |

## 🏗️ Architecture

### Three Independent Services

| Service | Port | Responsibility | Tech |
|---------|------|-----------------|------|
| **Authorization Server** | 5000 | Issues tokens, authenticates users | FastAPI |
| **Resource Server** | 5002 | Protects APIs, validates tokens | FastAPI |
| **Client App** | 5001 | Web app that accesses user data | Flask |

### Technology Stack

- **Language**: Python 3.9+
- **Web Frameworks**: FastAPI (async), Flask
- **Database**: PostgreSQL (production) / SQLite (local)
- **Authentication**: JWT tokens, secure cookies
- **Containerization**: Docker Compose for orchestration
- **Testing**: pytest with coverage

## 📂 Project Structure

```
OAuth2/
├── auth-server/                  # Authorization Server (both flows)
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # Database models (User, OAuthClient, Token, AuthorizationCode)
│   ├── security.py               # Token generation & validation (user + client tokens)
│   ├── routes.py                 # OAuth2 endpoints (handles both grant types)
│   ├── config.py                 # Configuration
│   ├── Dockerfile
│   └── requirements.txt
│
├── resource-server/              # Resource Server (protects both user and machine APIs)
│   ├── main.py                   # FastAPI app
│   ├── routes.py                 # User APIs + machine APIs (/api/service/*)
│   ├── security.py               # Token validation (@require_oauth2 for users, @require_client_token for machines)
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── client-app/                   # Client Web Application (Authorization Code Flow demo)
│   ├── main.py                   # Flask app
│   ├── auth.py                   # OAuth2 flow logic (PKCE, state, code exchange)
│   ├── routes.py                 # Web routes and callback handler
│   ├── templates/                # HTML templates
│   ├── Dockerfile
│   └── requirements.txt
│
├── migrations/                   # Alembic database migrations
├── tests/                        # Test suite
│   ├── auth_server/              # Auth server unit tests (both grant types)
│   ├── resource_server/          # Resource server endpoint tests
│   └── e2e/                      # End-to-end flow tests
├── scripts/
│   ├── seed.py                   # Seeds test users + both client registrations
│   └── service_client.py         # Client Credentials Flow demo (CLI, ~40 lines)
├── docker-compose.yml            # Docker Compose config
├── Makefile                      # Development commands
├── .env.example                  # Environment template
└── AGENTS.md                     # AI Agent customization guide
```

## 🚀 Development Commands

```bash
# Setup
make install                    # Install Python dependencies
make setup-env                  # Create .env file

# Running
make up                         # Start all services
make down                       # Stop services
make dev                        # Start with hot-reload
make logs                       # View logs

# Testing
make test                       # Run all tests
make test-e2e                   # End-to-end Authorization Code flow test
make test-e2e-cc                # End-to-end Client Credentials flow test
make coverage                   # Coverage report

# Demos
make demo-cc                    # Run service_client.py: prints token claims + API response

# Database
make migrate                    # Run migrations
make seed                       # Add test users + register both OAuth2 clients

# Cleanup
make clean                      # Remove containers & volumes
make clean-all                  # Deep clean
```

See `make help` for full list of commands.

## 🔐 Key Security Features

**Authorization Code Flow**
✅ **PKCE** (Proof Key for Code Exchange) - Prevents authorization code interception  
✅ **State Parameter** - CSRF protection during redirects  
✅ **Secure Cookies** - HttpOnly, Secure flags for refresh tokens  

**Client Credentials Flow**
✅ **Client Authentication** - client_id + client_secret validated server-side  
✅ **Scope Restriction** - Each machine client declares allowed scopes at registration  
✅ **No Refresh Token** - Stateless re-request model for machine clients  

**Both flows**
✅ **JWT Validation** - Token signature verification (or introspection mode)  
✅ **Token Expiry** - Short-lived access tokens  
✅ **HTTPS Ready** - TLS/SSL configuration for production  

## 📝 Configuration

Create `.env` from `.env.example`:

```bash
make setup-env
```

Key environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENV` | development | Environment (development/production) |
| `DEBUG` | true | Enable debug logging |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `DB_HOST` | postgres | PostgreSQL hostname |
| `AUTH_SERVER_URL` | http://localhost:5000 | Auth server URL |
| `OAUTH2_CLIENT_ID` | web-client | OAuth2 client ID |
| `OAUTH2_CLIENT_SECRET` | web-client-secret | OAuth2 client secret |

## 🧪 Testing

### Run All Tests
```bash
make test
```

### End-to-End OAuth2 Flow
```bash
make test-e2e
```

This test:
1. Creates a test user in Authorization Server
2. Starts OAuth2 flow from Client App
3. Authenticates user
4. Exchanges auth code for token
5. Calls Resource Server with token
6. Verifies protected data is returned

### Coverage Report
```bash
make coverage
open htmlcov/index.html
```

## 📊 Default Test Credentials

After running `make seed`, these are available:

**Users** (for Authorization Code flow)

| Username | Password | Email |
|----------|----------|-------|
| alice | alice123 | alice@example.com |
| bob | bob123 | bob@example.com |
| charlie | charlie123 | charlie@example.com |

**Registered OAuth2 Clients**

| Client ID | Secret | Grant type | Scopes |
|-----------|--------|------------|--------|
| `web-client` | `web-client-secret` | `authorization_code` | `read write` |
| `service-client` | `service-client-secret` | `client_credentials` | `read:stats` |

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
make logs

# Verify PostgreSQL is healthy
docker-compose ps

# Reset everything
make clean
make up
```

### "Invalid client credentials"
- Verify `OAUTH2_CLIENT_ID` and `OAUTH2_CLIENT_SECRET` in `.env`
- Check they match values registered in Authorization Server database

### "Token has expired"
- Access tokens expire every 15 minutes by default
- Use refresh token to get a new access token (automatic in client app)

### Database errors
```bash
# Run migrations
make migrate

# Seed with test data
make seed
```

## 🌐 URLs (Local Development)

- **Client App**: [http://localhost:5001](http://localhost:5001) - Start here!
- **Auth Server**: [http://localhost:5000](http://localhost:5000)
- **Resource Server**: [http://localhost:5002](http://localhost:5002)
- **PostgreSQL**: localhost:5432

## 📚 API Documentation

### Authorization Server

| Endpoint | Method | Description | Grant type |
|----------|--------|-------------|------------|
| `/authorize` | GET | Initiate Authorization Code flow | `authorization_code` |
| `/token` | POST | Exchange code **or** client credentials for token | both |
| `/refresh` | POST | Get new access token using refresh token | `authorization_code` |
| `/userinfo` | GET | Get current user info (requires user token) | `authorization_code` |
| `/introspect` | POST | Validate/introspect any token | both |
| `/.well-known/oauth-metadata` | GET | OpenID Connect discovery | — |

The `/token` endpoint distinguishes flows by `grant_type` in the request body:
- `grant_type=authorization_code` — requires `code`, `redirect_uri`, `code_verifier` (PKCE)
- `grant_type=client_credentials` — requires `client_id`, `client_secret`, `scope`

### Resource Server

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/user/profile` | GET | Get user profile | User Bearer token |
| `/api/user/data` | GET | Get user data | User Bearer token |
| `/api/service/stats` | GET | Aggregate stats (machine API) | Client Bearer token |
| `/health` | GET | Health check | None |

User endpoints use `@require_oauth2` (token must have a user `sub`).  
Machine endpoints use `@require_client_token` (token `sub` is a client ID, no user context).

### Client App (Authorization Code Flow)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page / login |
| `/callback` | GET | OAuth2 callback (internal) |
| `/profile` | GET | User profile (protected) |
| `/logout` | POST | Logout |

### Service Client (Client Credentials Flow)

A CLI script (`scripts/service_client.py`), not a web server. Run with:

```bash
python scripts/service_client.py
# or: make demo-cc
```

It prints the raw token claims, then calls `/api/service/stats` and shows the response. The entire OAuth2 Client Credentials flow in one file.

## 🔗 Learn More

- [AGENTS.md](AGENTS.md) - AI Agent customization guide
- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749) - Official spec
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636) - Proof Key for Code Exchange
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - FastAPI docs
- [OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html) - Identity layer

## 📄 License

MIT License - Feel free to use this for learning and projects!

## 🤝 Contributing

This is an educational project. Contributions and improvements are welcome!

---

**Ready to explore?** Start with `make up` and visit [http://localhost:5001](http://localhost:5001)
