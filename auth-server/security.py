from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


# ---------------------------------------------------------------------------
# Hashing — one function pair for both passwords and client secrets (same bcrypt)
# ---------------------------------------------------------------------------

def hash_value(value: str) -> str:
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()


def verify_value(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _build_payload(sub: str, token_type: str, scope: str) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": sub,
        "token_type": token_type,
        "scope": scope,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }


def create_user_token(user_id: int, scope: str) -> str:
    """Authorization Code flow token — sub is the user's integer ID (as string)."""
    payload = _build_payload(str(user_id), "user", scope)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_client_token(client_id: str, scope: str) -> str:
    """Client Credentials flow token — sub is the client_id string, not a user.
    No refresh token is issued alongside this; clients simply re-request.
    """
    payload = _build_payload(client_id, "client", scope)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.InvalidTokenError on any failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ---------------------------------------------------------------------------
# Authorization code + PKCE
# ---------------------------------------------------------------------------

def generate_code() -> str:
    """Cryptographically random opaque token (used for auth codes and refresh tokens)."""
    return secrets.token_urlsafe(32)


def verify_pkce(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Verify a PKCE challenge per RFC 7636."""
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return secrets.compare_digest(computed, code_challenge)
    # plain method — only for testing, not recommended in production
    return secrets.compare_digest(code_verifier, code_challenge)
