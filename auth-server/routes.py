from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES, AUTHORIZATION_CODE_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
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


# ---------------------------------------------------------------------------
# GET /authorize — show login form (RFC 6749 §4.1.1)
# POST /authorize — validate credentials and issue auth code (RFC 6749 §4.1.2)
# ---------------------------------------------------------------------------

def _login_page(
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str | None,
    code_challenge_method: str,
    error: str | None = None,
) -> str:
    """Return a minimal HTML login form. Hidden fields carry OAuth2 params through POST."""
    error_html = f'<p class="error">{error}</p>' if error else ""
    challenge_field = (
        f'<input type="hidden" name="code_challenge" value="{code_challenge}">'
        f'<input type="hidden" name="code_challenge_method" value="{code_challenge_method}">'
        if code_challenge else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sign in — OAuth2 Auth Server</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 380px; margin: 80px auto; padding: 0 1rem; color: #222; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
    .subtitle {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    label {{ display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; }}
    input[type=text], input[type=password] {{
      width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;
      font-size: 1rem; box-sizing: border-box; margin-bottom: 1rem;
    }}
    button {{ width: 100%; padding: 0.6rem; background: #2563eb; color: #fff;
      border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }}
    button:hover {{ background: #1d4ed8; }}
    .error {{ color: #dc2626; font-size: 0.9rem; margin-bottom: 1rem; }}
    .scope-box {{ background: #f1f5f9; border-radius: 4px; padding: 0.75rem; margin-bottom: 1.25rem; font-size: 0.85rem; }}
    .scope-box strong {{ display: block; margin-bottom: 0.25rem; }}
  </style>
</head>
<body>
  <h1>Sign in</h1>
  <p class="subtitle">Client <code>{client_id}</code> is requesting access.</p>
  <div class="scope-box">
    <strong>Requested scopes:</strong> {scope or "(none)"}
  </div>
  {error_html}
  <form method="post" action="/authorize">
    <input type="hidden" name="client_id" value="{client_id}">
    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
    <input type="hidden" name="scope" value="{scope}">
    <input type="hidden" name="state" value="{state}">
    {challenge_field}
    <label for="username">Username</label>
    <input type="text" id="username" name="username" required autofocus>
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required>
    <button type="submit">Sign in</button>
  </form>
</body>
</html>"""


def _error_page(error: str, description: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Error — OAuth2 Auth Server</title>
<style>body{{font-family:system-ui,sans-serif;max-width:480px;margin:80px auto;padding:0 1rem;}}
.box{{background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;padding:1.25rem;}}
h1{{color:#dc2626;font-size:1.2rem;margin:0 0 0.5rem;}}p{{margin:0;color:#555;font-size:0.9rem;}}</style>
</head><body>
<div class="box"><h1>{error}</h1><p>{description}</p></div>
</body></html>"""


@router.get("/authorize", response_class=HTMLResponse)
def authorize_get(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(""),
    state: str = Query(""),
    code_challenge: str | None = Query(None),
    code_challenge_method: str = Query("S256"),
    db: Session = Depends(get_db),
):
    """Display the login form. Validates client params before showing the form."""
    if response_type != "code":
        return HTMLResponse(_error_page("unsupported_response_type", "Only response_type=code is supported"), status_code=400)
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        return HTMLResponse(_error_page("invalid_client", f"Unknown client_id: {client_id!r}"), status_code=400)
    if redirect_uri not in (client.redirect_uris or []):
        return HTMLResponse(_error_page("invalid_request", "redirect_uri is not registered for this client"), status_code=400)
    if not client.allows_grant_type("authorization_code"):
        return HTMLResponse(_error_page("unauthorized_client", "This client may not use the authorization_code flow"), status_code=400)
    return HTMLResponse(_login_page(client_id, redirect_uri, scope, state, code_challenge, code_challenge_method))


@router.post("/authorize")
def authorize_post(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(""),
    state: str = Form(""),
    code_challenge: str | None = Form(None),
    code_challenge_method: str = Form("S256"),
    db: Session = Depends(get_db),
):
    """Process the login form. On success, redirect to client with auth code."""
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client or redirect_uri not in (client.redirect_uris or []):
        return HTMLResponse(_error_page("invalid_request", "Invalid client or redirect_uri"), status_code=400)

    def _redirect_error(error: str, description: str) -> RedirectResponse:
        qs = urlencode({"error": error, "error_description": description, "state": state})
        return RedirectResponse(f"{redirect_uri}?{qs}", status_code=302)

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_value(password, user.password_hash):
        return HTMLResponse(
            _login_page(client_id, redirect_uri, scope, state, code_challenge, code_challenge_method, error="Invalid username or password"),
            status_code=401,
        )

    if scope and not client.allows_scope(scope):
        return _redirect_error("invalid_scope", "One or more requested scopes are not allowed for this client")

    granted_scope = scope or " ".join(client.allowed_scopes or [])
    code = generate_code()
    auth_code = AuthorizationCode(
        code=code,
        scope=granted_scope,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method if code_challenge else None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=AUTHORIZATION_CODE_EXPIRE_MINUTES),
        client_id=client.id,
        user_id=user.id,
    )
    db.add(auth_code)
    db.commit()

    qs = urlencode({"code": code, "state": state})
    return RedirectResponse(f"{redirect_uri}?{qs}", status_code=302)


# ---------------------------------------------------------------------------
# Helpers for other endpoints
# ---------------------------------------------------------------------------

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

    access_token = create_user_token(auth_code.user_id, auth_code.scope)
    refresh_token = generate_code()

    db.add(Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="user",
        scope=auth_code.scope,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        user_id=auth_code.user_id,
        client_id=client.id,
    ))
    db.commit()

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
        .filter(Token.refresh_token == refresh_token, Token.client_id == client.id)
        .first()
    )
    if not stored or stored.revoked:
        _oauth2_error("invalid_grant", "Refresh token not found or already revoked")

    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        _oauth2_error("invalid_grant", "Refresh token has expired")

    new_access_token = create_user_token(stored.user_id, stored.scope)
    stored.access_token = new_access_token
    db.commit()

    return {
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": stored.scope,
        "refresh_token": refresh_token,
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
# GET /health
# ---------------------------------------------------------------------------

@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "db": str(exc)},
        )
    return {"status": "ok", "db": db_status}


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
