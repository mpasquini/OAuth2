"""Client app flow tests.

Covers the browser-side Authorization Code + PKCE flow:
  - /login redirects to auth server with correct params
  - /callback exchanges code for tokens (mocked HTTP)
  - /callback rejects state mismatch (CSRF check)
  - /profile requires a logged-in session
  - /logout clears the session
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).parents[2]
CLIENT = ROOT / "client-app"


def _load(path: Path, sys_name: str):
    spec = importlib.util.spec_from_file_location(sys_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[sys_name] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(CLIENT))   # lets Flask find templates/ relative to client-app/

_load(CLIENT / "config.py", "config")
_load(CLIENT / "auth.py", "auth")
# Keep a direct reference — sys.modules["routes"] may be overwritten by the
# resource-server test module (same key, different file) depending on collection order.
_ca_routes = _load(CLIENT / "routes.py", "routes")
client_main = _load(CLIENT / "main.py", "main")

app = client_main.app
app.config["TESTING"] = True
app.config["SECRET_KEY"] = "test-secret"


@pytest.fixture()
def client():
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# /login
# ---------------------------------------------------------------------------

def test_login_redirects_to_auth_server(client):
    """/login must redirect to the auth server /authorize endpoint."""
    r = client.get("/login")
    assert r.status_code == 302
    loc = r.headers["Location"]
    assert "authorize" in loc
    assert "response_type=code" in loc
    assert "code_challenge=" in loc
    assert "state=" in loc


def test_login_sets_session_state(client):
    """state and code_verifier must be stored in the session before redirect."""
    with client.session_transaction() as pre:
        assert "oauth_state" not in pre

    client.get("/login")

    with client.session_transaction() as post:
        assert "oauth_state" in post
        assert "code_verifier" in post


# ---------------------------------------------------------------------------
# /callback
# ---------------------------------------------------------------------------

def test_callback_invalid_state_rejected(client):
    """Mismatched state must not result in a token exchange."""
    with client.session_transaction() as sess:
        sess["oauth_state"] = "correct-state"
        sess["code_verifier"] = "some-verifier"

    r = client.get("/callback?code=abc&state=wrong-state")
    assert r.status_code == 200
    assert b"State mismatch" in r.data


def test_callback_exchanges_code_for_token(client):
    """Valid state + code must call exchange_code and store tokens in session."""
    with client.session_transaction() as sess:
        sess["oauth_state"] = "correct-state"
        sess["code_verifier"] = "test-verifier"

    fake_tokens = {
        "access_token": "header.payload.sig",
        "refresh_token": "refresh-tok",
        "scope": "read write",
        "token_type": "Bearer",
        "expires_in": 900,
    }

    with patch.object(_ca_routes, "exchange_code", return_value=fake_tokens) as mock_exchange:
        r = client.get("/callback?code=auth-code-123&state=correct-state")

    mock_exchange.assert_called_once_with("auth-code-123", "test-verifier")
    assert r.status_code == 302
    assert "/profile" in r.headers["Location"]

    with client.session_transaction() as sess:
        assert sess["access_token"] == "header.payload.sig"
        assert sess["refresh_token"] == "refresh-tok"


def test_callback_error_param_shows_error(client):
    """Auth server error redirect must display an error, not crash."""
    r = client.get("/callback?error=access_denied&error_description=User+denied")
    assert r.status_code == 200
    assert b"access_denied" in r.data


# ---------------------------------------------------------------------------
# /profile
# ---------------------------------------------------------------------------

def test_profile_requires_login(client):
    """/profile must redirect to /login when no session token is present."""
    r = client.get("/profile")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_profile_shows_claims(client):
    """Logged-in user should see decoded token claims on the profile page."""
    import jwt

    token = jwt.encode(
        {"sub": "42", "token_type": "user", "scope": "read", "iat": 0, "exp": 9999999999},
        "any-key",
        algorithm="HS256",
    )

    with client.session_transaction() as sess:
        sess["access_token"] = token
        sess["scope"] = "read"

    fake_profile = {"sub": "42", "scope": "read", "token_type": "user"}

    with patch.object(_ca_routes, "get_user_profile", return_value=fake_profile):
        r = client.get("/profile")

    assert r.status_code == 200
    assert b"token_type" in r.data
    assert b"user" in r.data


# ---------------------------------------------------------------------------
# /logout
# ---------------------------------------------------------------------------

def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["access_token"] = "some-token"
        sess["refresh_token"] = "some-refresh"

    r = client.get("/logout")
    assert r.status_code == 302

    with client.session_transaction() as sess:
        assert "access_token" not in sess
        assert "refresh_token" not in sess
