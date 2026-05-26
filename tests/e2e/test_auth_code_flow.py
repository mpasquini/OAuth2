"""End-to-end Authorization Code flow test.

Requires all services to be running (make up).
Tests the full browser-based path without a real browser:
  /authorize (GET login form) → POST credentials → extract code from redirect
  → POST /token (code exchange + PKCE) → GET /api/user/profile

Run with: make test-e2e
"""
import secrets
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
import requests

from helpers import (
    AC_CLIENT_ID,
    AC_CLIENT_SECRET,
    AC_REDIRECT_URI,
    AUTH_SERVER_URL,
    RESOURCE_SERVER_URL,
    TEST_PASSWORD,
    TEST_USERNAME,
    generate_pkce,
)


def _do_auth_code_flow(username: str = TEST_USERNAME, password: str = TEST_PASSWORD) -> dict:
    """Simulate the full Authorization Code + PKCE flow programmatically.

    Returns the full token response dict (access_token, refresh_token, scope, …).
    Raises on any unexpected HTTP status so test failures are obvious.
    """
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    # Step 1 — redirect user to auth server (verify the form is served)
    r = requests.get(f"{AUTH_SERVER_URL}/authorize", params={
        "response_type": "code",
        "client_id": AC_CLIENT_ID,
        "redirect_uri": AC_REDIRECT_URI,
        "scope": "read write",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    assert r.status_code == 200, f"/authorize GET failed: {r.status_code}"
    assert "form" in r.text.lower()

    # Step 2 — submit login credentials; do NOT follow the redirect
    r = requests.post(
        f"{AUTH_SERVER_URL}/authorize",
        data={
            "username": username,
            "password": password,
            "client_id": AC_CLIENT_ID,
            "redirect_uri": AC_REDIRECT_URI,
            "scope": "read write",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
        allow_redirects=False,
    )
    assert r.status_code in (302, 303), f"/authorize POST returned {r.status_code}"

    location = r.headers.get("Location", "")
    parsed = urlparse(location)
    qs = parse_qs(parsed.query)

    assert "code" in qs, f"No code in redirect: {location}"
    assert qs.get("state", [None])[0] == state, "state mismatch"

    code = qs["code"][0]

    # Step 3 — exchange code for tokens (PKCE verifier must match challenge)
    r = requests.post(f"{AUTH_SERVER_URL}/token", data={
        "grant_type": "authorization_code",
        "client_id": AC_CLIENT_ID,
        "client_secret": AC_CLIENT_SECRET,
        "code": code,
        "redirect_uri": AC_REDIRECT_URI,
        "code_verifier": code_verifier,
    })
    assert r.status_code == 200, f"/token returned {r.status_code}: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# Token issuance
# ---------------------------------------------------------------------------

class TestAuthCodeToken:
    @pytest.fixture(scope="class")
    def tokens(self):
        return _do_auth_code_flow()

    def test_returns_access_and_refresh_token(self, tokens):
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"

    def test_token_claims(self, tokens):
        """Token sub must be the user ID (not client_id); token_type must be 'user'."""
        claims = jwt.decode(tokens["access_token"], options={"verify_signature": False})
        assert claims["token_type"] == "user"
        # sub is the integer user ID serialised as a string
        assert claims["sub"].isdigit()

    def test_scope_returned(self, tokens):
        assert "read" in tokens.get("scope", "")

    def test_code_is_single_use(self):
        """Replaying the same code must return invalid_grant (RFC 6749 §10.5)."""
        code_verifier, code_challenge = generate_pkce()
        state = secrets.token_urlsafe(16)

        r = requests.post(
            f"{AUTH_SERVER_URL}/authorize",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "client_id": AC_CLIENT_ID,
                "redirect_uri": AC_REDIRECT_URI,
                "scope": "read",
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            },
            allow_redirects=False,
        )
        code = parse_qs(urlparse(r.headers["Location"]).query)["code"][0]

        exchange_data = {
            "grant_type": "authorization_code",
            "client_id": AC_CLIENT_ID,
            "client_secret": AC_CLIENT_SECRET,
            "code": code,
            "redirect_uri": AC_REDIRECT_URI,
            "code_verifier": code_verifier,
        }
        r1 = requests.post(f"{AUTH_SERVER_URL}/token", data=exchange_data)
        assert r1.status_code == 200

        r2 = requests.post(f"{AUTH_SERVER_URL}/token", data=exchange_data)
        assert r2.status_code == 400
        assert r2.json()["detail"]["error"] == "invalid_grant"

    def test_wrong_code_verifier_rejected(self):
        """PKCE: wrong verifier must be rejected (RFC 7636 §4.6)."""
        _, code_challenge = generate_pkce()
        state = secrets.token_urlsafe(16)

        r = requests.post(
            f"{AUTH_SERVER_URL}/authorize",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "client_id": AC_CLIENT_ID,
                "redirect_uri": AC_REDIRECT_URI,
                "scope": "read",
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            },
            allow_redirects=False,
        )
        code = parse_qs(urlparse(r.headers["Location"]).query)["code"][0]

        r = requests.post(f"{AUTH_SERVER_URL}/token", data={
            "grant_type": "authorization_code",
            "client_id": AC_CLIENT_ID,
            "client_secret": AC_CLIENT_SECRET,
            "code": code,
            "redirect_uri": AC_REDIRECT_URI,
            "code_verifier": "wrong-verifier",
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_grant"

    def test_bad_password_redirects_with_error_html(self):
        """Wrong credentials must return 401 (re-render login form, not redirect)."""
        r = requests.post(
            f"{AUTH_SERVER_URL}/authorize",
            data={
                "username": TEST_USERNAME,
                "password": "wrong-password",
                "client_id": AC_CLIENT_ID,
                "redirect_uri": AC_REDIRECT_URI,
                "scope": "read",
                "state": "any",
                "code_challenge": "anychallenge",
                "code_challenge_method": "S256",
            },
            allow_redirects=False,
        )
        assert r.status_code == 401
        assert "Invalid" in r.text


# ---------------------------------------------------------------------------
# Resource server access
# ---------------------------------------------------------------------------

class TestAuthCodeResourceAccess:
    @pytest.fixture(scope="class")
    def access_token(self):
        return _do_auth_code_flow()["access_token"]

    def test_profile_returns_200(self, access_token):
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/user/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert r.status_code == 200

    def test_profile_response_shape(self, access_token):
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/user/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        body = r.json()
        assert body["token_type"] == "user"
        assert "sub" in body

    def test_user_token_rejected_on_machine_endpoint(self, access_token):
        """User token must be rejected by /api/service/stats with 403 (RFC 9700 §2.3)."""
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/service/stats",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert r.status_code == 403
        assert r.json()["detail"]["error"] == "insufficient_scope"

    def test_no_token_rejected(self):
        r = requests.get(f"{RESOURCE_SERVER_URL}/api/user/profile")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

class TestTokenRefresh:
    def test_refresh_yields_new_access_token(self):
        tokens = _do_auth_code_flow()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            pytest.skip("No refresh_token in token response")

        r = requests.post(f"{AUTH_SERVER_URL}/refresh", data={
            "refresh_token": refresh_token,
            "client_id": AC_CLIENT_ID,
            "client_secret": AC_CLIENT_SECRET,
        })
        # NOTE: /refresh is currently broken (refresh token not persisted — PLAN RFC9700 review).
        # This test documents the expected behaviour for when it is fixed.
        if r.status_code == 400 and r.json().get("detail", {}).get("error") == "invalid_grant":
            pytest.xfail("refresh token not persisted yet — see PLAN.md RFC 9700 review")
        assert r.status_code == 200
        new_tokens = r.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
