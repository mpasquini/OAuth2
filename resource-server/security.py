from __future__ import annotations

import jwt
import httpx
from fastapi import Depends, HTTPException, Request

from config import (
    AUTH_SERVER_ALGORITHM,
    AUTH_SERVER_SECRET_KEY,
    AUTH_SERVER_INTROSPECTION_URL,
    INTROSPECTION_CLIENT_ID,
    INTROSPECTION_CLIENT_SECRET,
    TOKEN_VALIDATION_MODE,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _extract_bearer(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            detail={"error": "invalid_request", "error_description": "Bearer token required"},
        )
    return auth[7:]


def _validate_token(token: str) -> dict:
    """Decode and validate a token. Mode is selected by TOKEN_VALIDATION_MODE."""
    if TOKEN_VALIDATION_MODE == "introspection":
        return _introspect(token)
    return _decode_jwt(token)


def _decode_jwt(token: str) -> dict:
    """JWT mode — verify signature locally with the shared secret. No network call."""
    try:
        return jwt.decode(token, AUTH_SERVER_SECRET_KEY, algorithms=[AUTH_SERVER_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "expired_token", "error_description": "Token has expired"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "error_description": str(exc)},
        )


def _introspect(token: str) -> dict:
    """Introspection mode — ask the auth-server. Slower but handles revoked tokens."""
    try:
        response = httpx.post(
            AUTH_SERVER_INTROSPECTION_URL,
            data={
                "token": token,
                "client_id": INTROSPECTION_CLIENT_ID,
                "client_secret": INTROSPECTION_CLIENT_SECRET,
            },
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail={"error": "temporarily_unavailable", "error_description": "Could not reach auth server"},
        )

    payload = response.json()
    if not payload.get("active"):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "error_description": "Token is inactive or revoked"},
        )
    return payload


# ---------------------------------------------------------------------------
# FastAPI dependencies — one per token type
# ---------------------------------------------------------------------------

def require_oauth2(request: Request) -> dict:
    """Dependency for user endpoints (Authorization Code flow).

    Validates the Bearer token and asserts token_type == 'user'.
    Populates request.state.oauth2_user with the token payload.

    Usage:
        @router.get("/api/user/profile")
        async def profile(request: Request, _=Depends(require_oauth2)):
            user = request.state.oauth2_user
    """
    token = _extract_bearer(request)
    payload = _validate_token(token)

    if payload.get("token_type") != "user":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_scope",
                "error_description": "This endpoint requires a user token (Authorization Code flow)",
            },
        )

    request.state.oauth2_user = payload
    return payload


def require_client_token(request: Request) -> dict:
    """Dependency for machine endpoints (Client Credentials flow).

    Validates the Bearer token and asserts token_type == 'client'.
    Populates request.state.oauth2_client with the token payload.

    Usage:
        @router.get("/api/service/stats")
        async def stats(request: Request, _=Depends(require_client_token)):
            client_id = request.state.oauth2_client["sub"]
    """
    token = _extract_bearer(request)
    payload = _validate_token(token)

    if payload.get("token_type") != "client":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_scope",
                "error_description": "This endpoint requires a client token (Client Credentials flow)",
            },
        )

    request.state.oauth2_client = payload
    return payload
