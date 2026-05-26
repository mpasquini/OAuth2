"""OAuth2 Authorization Code + PKCE helpers for the client app.

Flow summary (RFC 6749 §4.1 + RFC 7636):
  1. generate_pkce()          → code_verifier, code_challenge
  2. build_authorize_url()    → redirect user to auth server /authorize
  3. exchange_code()          → POST /token, get access + refresh tokens
  4. refresh_access_token()   → POST /refresh, get new access token
  5. get_user_profile()       → GET /api/user/profile on resource server
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import requests

from config import (
    AUTHORIZE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_SCOPE,
    REDIRECT_URI,
    REFRESH_URL,
    RESOURCE_SERVER_URL,
    TOKEN_URL,
)


def generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256 method (RFC 7636 §4.1).

    code_verifier  — high-entropy random string, stored in session
    code_challenge — SHA-256 hash of verifier, sent to auth server
    """
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str, scope: str = DEFAULT_SCOPE) -> str:
    """Build the /authorize URL the user's browser is redirected to."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str, code_verifier: str) -> dict:
    """Exchange the one-time auth code for tokens (RFC 6749 §4.1.3).

    Returns the full token response dict:
      access_token, token_type, expires_in, scope, refresh_token
    """
    r = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Obtain a fresh access token using the refresh token (RFC 6749 §6).

    Returns a new token response (no new refresh_token — caller keeps the old one).
    """
    r = requests.post(REFRESH_URL, data={
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def get_user_profile(access_token: str) -> dict:
    """Fetch /api/user/profile from the resource server using the bearer token."""
    r = requests.get(
        f"{RESOURCE_SERVER_URL}/api/user/profile",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()
