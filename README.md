# OAuth2 Implementation - Authorization Code Flow

A **practical, educational, and production-ready** implementation of OAuth2 authorization code flow with three distinct components running in Docker containers.

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

## 🔄 OAuth2 Authorization Code Flow

This project demonstrates the complete OAuth2 cycle:

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
├── auth-server/                  # Authorization Server
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # Database models
│   ├── security.py               # Token generation & validation
│   ├── routes.py                 # OAuth2 endpoints
│   ├── config.py                 # Configuration
│   ├── Dockerfile
│   └── requirements.txt
│
├── resource-server/              # Resource Server
│   ├── main.py                   # FastAPI app
│   ├── routes.py                 # Protected APIs
│   ├── security.py               # Token validation middleware
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── client-app/                   # Client Web Application
│   ├── main.py                   # Flask app
│   ├── auth.py                   # OAuth2 flow logic
│   ├── routes.py                 # Web routes
│   ├── templates/                # HTML templates
│   ├── Dockerfile
│   └── requirements.txt
│
├── migrations/                   # Alembic database migrations
├── tests/                        # Test suite
├── scripts/                      # Utilities (seed.py, etc.)
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
make test-e2e                   # End-to-end flow test
make coverage                   # Coverage report

# Database
make migrate                    # Run migrations
make seed                       # Add test users

# Cleanup
make clean                      # Remove containers & volumes
make clean-all                  # Deep clean
```

See `make help` for full list of commands.

## 🔐 Key Security Features

✅ **PKCE** (Proof Key for Code Exchange) - Prevents authorization code interception  
✅ **State Parameter** - CSRF protection during redirects  
✅ **Secure Cookies** - HttpOnly, Secure flags for refresh tokens  
✅ **JWT Validation** - Token signature verification  
✅ **Token Expiry** - Short-lived access tokens, long-lived refresh tokens  
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

## 📊 Default Test Users

After running `make seed`, these users are available:

| Username | Password | Email |
|----------|----------|-------|
| alice | alice123 | alice@example.com |
| bob | bob123 | bob@example.com |
| charlie | charlie123 | charlie@example.com |

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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/authorize` | GET | Initiate OAuth2 flow |
| `/token` | POST | Exchange code for token |
| `/refresh` | POST | Get new access token using refresh token |
| `/userinfo` | GET | Get current user info (requires token) |
| `/introspect` | POST | Validate/introspect token |
| `/.well-known/oauth-metadata` | GET | OpenID Connect discovery |

### Resource Server

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/user/profile` | GET | Get user profile | Bearer token |
| `/api/user/data` | GET | Get user data | Bearer token |
| `/health` | GET | Health check | None |

### Client App

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page / login |
| `/callback` | GET | OAuth2 callback (internal) |
| `/profile` | GET | User profile (protected) |
| `/logout` | POST | Logout |

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
