from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models import AuthorizationCode, OAuthClient, Token, User
from security import (
    create_client_token,
    create_user_token,
    decode_token,
    generate_code,
    verify_pkce,
    verify_value,
)

router = APIRouter()


def _oauth2_error(error: str, description: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"error": error, "error_description": description},
    )


# ---------------------------------------------------------------------------
# POST /token — handles both grant types
# ---------------------------------------------------------------------------

@router.post("/token")
def token_endpoint(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    # Authorization Code fields
    code: str | None = Form(None),
    redirect_uri: str | None = Form(None),
    code_verifier: str | None = Form(None),
    # Client Credentials / scope
    scope: str = Form(""),
    db: Session = Depends(get_db),
):
    """Token endpoint — RFC 6749 §3.2.

    Dispatches to the correct flow based on grant_type:
      - authorization_code: exchanges a one-time auth code for tokens (user flow)
      - client_credentials: authenticates a machine client directly (no user)
    """
    # Validate client identity first — same for both flows.
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client or not verify_value(client_secret, client.client_secret_hash):
        _oauth2_error("invalid_client", "Invalid client credentials", status_code=401)

    if not client.allows_grant_type(grant_type):
        _oauth2_error(
            "unauthorized_client",
            f"This client is not authorized to use grant_type={grant_type!r}",
        )

    if grant_type == "client_credentials":
        return _client_credentials(client, scope)

    if grant_type == "authorization_code":
        return _authorization_code(client, code, redirect_uri, code_verifier, db)

    _oauth2_error("unsupported_grant_type", f"grant_type={grant_type!r} is not supported")


def _client_credentials(client: OAuthClient, requested_scope: str) -> dict:
    """Client Credentials flow (RFC 6749 §4.4).

    No user is involved. The issued token's sub is the client_id itself.
    No refresh token — clients simply request a new token when it expires.
    """
    if requested_scope and not client.allows_scope(requested_scope):
        _oauth2_error(
            "invalid_scope",
            "One or more requested scopes are not allowed for this client",
        )

    # Fall back to all allowed scopes when the client doesn't specify.
    granted_scope = requested_scope or " ".join(client.allowed_scopes or [])
    access_token = create_client_token(client.client_id, granted_scope)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": granted_scope,
        # Deliberately no refresh_token field — RFC 6749 §4.4.3
    }


def _authorization_code(
    client: OAuthClient,
    code: str | None,
    redirect_uri: str | None,
    code_verifier: str | None,
    db: Session,
) -> dict:
    """Authorization Code flow (RFC 6749 §4.1) with PKCE (RFC 7636).

    Exchanges a short-lived auth code for an access token + refresh token.
    The token's sub is the integer user ID.
    """
    if not code:
        _oauth2_error("invalid_request", "code is required for grant_type=authorization_code")
    if not redirect_uri:
        _oauth2_error("invalid_request", "redirect_uri is required for grant_type=authorization_code")

    auth_code = (
        db.query(AuthorizationCode)
        .filter(
            AuthorizationCode.code == code,
            AuthorizationCode.client_id == client.id,
        )
        .first()
    )
    if not auth_code:
        _oauth2_error("invalid_grant", "Authorization code not found or does not belong to this client")
    if auth_code.used:
        # Possible replay attack — RFC 6749 §10.5 recommends revoking all tokens
        # issued for this code. Kept simple here for clarity.
        _oauth2_error("invalid_grant", "Authorization code has already been used. Possible replay attack — RFC 6749 §10.5 recommends revoking all tokens")
    if auth_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        _oauth2_error("invalid_grant", "Authorization code has expired")
    if auth_code.redirect_uri != redirect_uri:
        _oauth2_error("invalid_grant", "redirect_uri does not match the one used at /authorize")

    # PKCE verification — required when the code was issued with a challenge.
    if auth_code.code_challenge:
        if not code_verifier:
            _oauth2_error("invalid_request", "code_verifier is required (PKCE was used at /authorize)")
        if not verify_pkce(
            code_verifier, auth_code.code_challenge, auth_code.code_challenge_method or "S256"
        ):
            _oauth2_error("invalid_grant", "PKCE code_verifier does not match code_challenge")

    auth_code.used = True
    db.commit()

    access_token = create_user_token(auth_code.user_id, auth_code.scope)
    refresh_token = generate_code()

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": auth_code.scope,
        "refresh_token": refresh_token,
    }


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post("/refresh")
def refresh_endpoint(
    refresh_token: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: Session = Depends(get_db),
):
    """Refresh token endpoint — Authorization Code flow only (RFC 6749 §6).
    Client Credentials clients re-authenticate instead of using refresh tokens.
    """
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client or not verify_value(client_secret, client.client_secret_hash):
        _oauth2_error("invalid_client", "Invalid client credentials", status_code=401)

    stored = (
        db.query(Token)
        .filter(Token.access_token == refresh_token, Token.client_id == client.id)
        .first()
    )
    if not stored or stored.revoked:
        _oauth2_error("invalid_grant", "Refresh token not found or already revoked")

    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        _oauth2_error("invalid_grant", "Refresh token has expired")

    new_token = create_user_token(stored.user_id, stored.scope)
    return {
        "access_token": new_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": stored.scope,
    }


# ---------------------------------------------------------------------------
# POST /introspect
# ---------------------------------------------------------------------------

@router.post("/introspect")
def introspect_endpoint(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: Session = Depends(get_db),
):
    """Token introspection (RFC 7662). Works for both user and client tokens."""
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client or not verify_value(client_secret, client.client_secret_hash):
        _oauth2_error("invalid_client", "Invalid client credentials", status_code=401)

    try:
        payload = decode_token(token)
    except Exception:
        return {"active": False}

    return {
        "active": True,
        "sub": payload.get("sub"),
        "token_type": payload.get("token_type"),
        "scope": payload.get("scope", ""),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
    }


# ---------------------------------------------------------------------------
# GET /.well-known/oauth-metadata
# ---------------------------------------------------------------------------

@router.get("/.well-known/oauth-metadata")
def oauth_metadata(request_url: str = ""):
    return {
        "issuer": "http://localhost:5000",
        "authorization_endpoint": "http://localhost:5000/authorize",
        "token_endpoint": "http://localhost:5000/token",
        "introspection_endpoint": "http://localhost:5000/introspect",
        "userinfo_endpoint": "http://localhost:5000/userinfo",
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
    }
