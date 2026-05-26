"""Shared constants and utilities for e2e tests."""
import base64
import hashlib
import os
import secrets

AUTH_SERVER_URL = os.getenv("TEST_AUTH_SERVER_URL", "http://localhost:5000")
RESOURCE_SERVER_URL = os.getenv("TEST_RESOURCE_SERVER_URL", "http://localhost:5002")

CC_CLIENT_ID = os.getenv("SERVICE_CLIENT_ID", "service-client")
CC_CLIENT_SECRET = os.getenv("SERVICE_CLIENT_SECRET", "service-client-secret")
CC_SCOPE = os.getenv("SERVICE_CLIENT_SCOPES", "read:stats")

AC_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "web-client")
AC_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "web-client-secret")
AC_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:5001/callback")

TEST_USERNAME = "alice"
TEST_PASSWORD = "alice-password"


def generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256 (RFC 7636 §4)."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge
