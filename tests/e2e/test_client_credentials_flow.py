"""End-to-end Client Credentials flow test.

Requires all services to be running (make up).
Tests the full machine-to-machine path:
  service-client → auth-server /token → resource-server /api/service/stats

Run with: make test-e2e-cc
"""
import jwt
import pytest
import requests

from helpers import (
    AUTH_SERVER_URL,
    CC_CLIENT_ID,
    CC_CLIENT_SECRET,
    CC_SCOPE,
    RESOURCE_SERVER_URL,
)


def _get_client_token(scope: str = CC_SCOPE) -> dict:
    """POST /token with client_credentials and return the full response body."""
    r = requests.post(f"{AUTH_SERVER_URL}/token", data={
        "grant_type": "client_credentials",
        "client_id": CC_CLIENT_ID,
        "client_secret": CC_CLIENT_SECRET,
        "scope": scope,
    })
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Token issuance
# ---------------------------------------------------------------------------

class TestClientCredentialsToken:
    def test_returns_access_token(self):
        body = _get_client_token()
        assert "access_token" in body
        assert body["token_type"] == "Bearer"
        assert "expires_in" in body

    def test_no_refresh_token(self):
        """RFC 6749 §4.4.3 — no refresh_token in client credentials response."""
        body = _get_client_token()
        assert "refresh_token" not in body

    def test_token_claims(self):
        """Token sub must be the client_id; token_type must be 'client'."""
        body = _get_client_token()
        claims = jwt.decode(body["access_token"], options={"verify_signature": False})
        assert claims["sub"] == CC_CLIENT_ID
        assert claims["token_type"] == "client"
        assert CC_SCOPE in claims.get("scope", "")

    def test_scope_returned(self):
        body = _get_client_token(scope="read:stats")
        assert body["scope"] == "read:stats"

    def test_invalid_secret_rejected(self):
        r = requests.post(f"{AUTH_SERVER_URL}/token", data={
            "grant_type": "client_credentials",
            "client_id": CC_CLIENT_ID,
            "client_secret": "wrong-secret",
        })
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "invalid_client"

    def test_out_of_scope_rejected(self):
        r = requests.post(f"{AUTH_SERVER_URL}/token", data={
            "grant_type": "client_credentials",
            "client_id": CC_CLIENT_ID,
            "client_secret": CC_CLIENT_SECRET,
            "scope": "write:admin",
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_scope"


# ---------------------------------------------------------------------------
# Resource server access
# ---------------------------------------------------------------------------

class TestClientCredentialsResourceAccess:
    @pytest.fixture(scope="class")
    def token(self):
        return _get_client_token()["access_token"]

    def test_stats_endpoint_returns_200(self, token):
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/service/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    def test_stats_response_shape(self, token):
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/service/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = r.json()
        assert body["requested_by"] == CC_CLIENT_ID
        assert "stats" in body
        assert "total_users" in body["stats"]

    def test_client_token_rejected_on_user_endpoint(self, token):
        """Client tokens must not access user-scoped endpoints (RFC 9700 §2.3)."""
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/user/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403
        assert r.json()["detail"]["error"] == "insufficient_scope"

    def test_no_token_rejected(self):
        r = requests.get(f"{RESOURCE_SERVER_URL}/api/service/stats")
        assert r.status_code == 401

    def test_expired_token_rejected(self):
        """A token with exp in the past must be rejected with 401."""
        from datetime import datetime, timedelta, timezone

        expired = jwt.encode(
            {
                "sub": CC_CLIENT_ID,
                "token_type": "client",
                "scope": CC_SCOPE,
                "iat": datetime.now(timezone.utc) - timedelta(hours=2),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            # Uses the default dev secret — matches auth-server/config.py default.
            key="change-me-in-production",
            algorithm="HS256",
        )
        r = requests.get(
            f"{RESOURCE_SERVER_URL}/api/service/stats",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert r.status_code == 401
