import os

# Shared secret with the auth-server for local JWT validation.
AUTH_SERVER_SECRET_KEY = os.getenv("AUTH_SERVER_SECRET_KEY", "change-me-in-production")
AUTH_SERVER_ALGORITHM = os.getenv("AUTH_SERVER_ALGORITHM", "HS256")

# Switch between local JWT decoding and remote introspection.
# "jwt"          — validate token signature locally (fast, no network call)
# "introspection" — ask the auth-server (slower, handles revoked tokens)
TOKEN_VALIDATION_MODE = os.getenv("TOKEN_VALIDATION_MODE", "jwt")

AUTH_SERVER_INTROSPECTION_URL = os.getenv(
    "AUTH_SERVER_INTROSPECTION_URL",
    "http://auth-server:5000/introspect",
)

# Credentials used when calling /introspect (resource-server acts as a client).
INTROSPECTION_CLIENT_ID = os.getenv("INTROSPECTION_CLIENT_ID", "resource-server")
INTROSPECTION_CLIENT_SECRET = os.getenv("INTROSPECTION_CLIENT_SECRET", "resource-server-secret")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5001",
).split(",")
