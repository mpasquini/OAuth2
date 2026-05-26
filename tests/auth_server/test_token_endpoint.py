"""Auth server token endpoint tests.

Covers both grant types on POST /token:
  - client_credentials: direct client auth, no refresh token issued (RFC 6749 §4.4)
  - authorization_code: code exchange, PKCE verification, one-time use (RFC 6749 §4.1)
"""
import base64
import hashlib
import importlib.util
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).parents[2]
AUTH = ROOT / "auth-server"

# Force test config before any auth-server module is loaded so that
# `from config import ...` at module level picks up test values.
os.environ.setdefault("AUTH_SERVER_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUTH_SERVER_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")


def _load(path: Path, sys_name: str):
    """Load a module from an explicit path and register it in sys.modules."""
    spec = importlib.util.spec_from_file_location(sys_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[sys_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Register auth-server config first so all subsequent imports resolve correctly.
_load(AUTH / "config.py", "config")
_load(AUTH / "security.py", "security")
_load(AUTH / "models.py", "models")
# database.py reads DATABASE_URL from config at load time; override before loading.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
_load(AUTH / "config.py", "config")   # reload with updated env
_load(AUTH / "database.py", "database")
_load(AUTH / "routes.py", "routes")
auth_main = _load(AUTH / "main.py", "main")

import models as _models          # noqa: E402 (loaded above)
import security as _security      # noqa: E402
from database import get_db       # noqa: E402


# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------

# StaticPool shares one in-memory connection across all sessions so that
# tables created in setup_db are visible to every session in the test run.
_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


auth_main.app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create tables once for all tests in this module."""
    _models.Base.metadata.create_all(_TEST_ENGINE)
    yield
    _models.Base.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture(scope="module")
def db_session():
    return _TestSession()


@pytest.fixture(scope="module")
def cc_client(db_session):
    """OAuthClient configured for client_credentials flow."""
    c = _models.OAuthClient(
        client_id="svc-client",
        client_secret_hash=_security.hash_value("svc-secret"),
        name="Service Client",
        redirect_uris=[],
        allowed_grant_types=["client_credentials"],
        allowed_scopes=["read:stats"],
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture(scope="module")
def ac_client(db_session):
    """OAuthClient configured for authorization_code flow."""
    c = _models.OAuthClient(
        client_id="web-client",
        client_secret_hash=_security.hash_value("web-secret"),
        name="Web Client",
        redirect_uris=["http://localhost:5001/callback"],
        allowed_grant_types=["authorization_code"],
        allowed_scopes=["read", "write"],
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture(scope="module")
def test_user(db_session):
    u = _models.User(
        username="alice",
        email="alice@example.com",
        password_hash=_security.hash_value("alice-pass"),
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture()
def client():
    return TestClient(auth_main.app)


def _make_pkce_pair():
    """Return (code_verifier, code_challenge) using S256 method."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _issue_auth_code(db_session, ac_client, user, pkce: bool = True) -> tuple:
    """Insert a fresh AuthorizationCode row and return (code, verifier)."""
    verifier, challenge = _make_pkce_pair()
    code = secrets.token_urlsafe(32)
    ac = _models.AuthorizationCode(
        code=code,
        scope="read",
        redirect_uri="http://localhost:5001/callback",
        code_challenge=challenge if pkce else None,
        code_challenge_method="S256" if pkce else None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        used=False,
        client_id=ac_client.id,
        user_id=user.id,
    )
    db_session.add(ac)
    db_session.commit()
    return code, verifier


# ---------------------------------------------------------------------------
# Client Credentials tests
# ---------------------------------------------------------------------------

class TestClientCredentials:
    def test_returns_access_token(self, client, cc_client, setup_db):
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
            "scope": "read:stats",
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "Bearer"
        assert body["scope"] == "read:stats"

    def test_no_refresh_token(self, client, cc_client, setup_db):
        """RFC 6749 §4.4.3 — no refresh_token in client credentials response."""
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
        })
        assert r.status_code == 200
        assert "refresh_token" not in r.json()

    def test_token_sub_is_client_id(self, client, cc_client, setup_db):
        """Token sub must identify the client, not a user."""
        import jwt as _jwt
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
        })
        payload = _jwt.decode(r.json()["access_token"], options={"verify_signature": False})
        assert payload["sub"] == "svc-client"
        assert payload["token_type"] == "client"

    def test_scope_defaults_to_allowed_scopes(self, client, cc_client, setup_db):
        """When no scope is requested the client's full allowed_scopes is granted."""
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
        })
        assert r.status_code == 200
        assert r.json()["scope"] == "read:stats"

    def test_invalid_scope_rejected(self, client, cc_client, setup_db):
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
            "scope": "write:admin",  # not in allowed_scopes
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_scope"


# ---------------------------------------------------------------------------
# Authorization Code tests
# ---------------------------------------------------------------------------

class TestAuthorizationCode:
    def test_valid_exchange_returns_tokens(self, client, ac_client, test_user, db_session, setup_db):
        code, verifier = _issue_auth_code(db_session, ac_client, test_user)
        r = client.post("/token", data={
            "grant_type": "authorization_code",
            "client_id": "web-client",
            "client_secret": "web-secret",
            "code": code,
            "redirect_uri": "http://localhost:5001/callback",
            "code_verifier": verifier,
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "Bearer"

    def test_code_is_single_use(self, client, ac_client, test_user, db_session, setup_db):
        """Replaying the same code must return invalid_grant."""
        code, verifier = _issue_auth_code(db_session, ac_client, test_user)
        data = {
            "grant_type": "authorization_code",
            "client_id": "web-client",
            "client_secret": "web-secret",
            "code": code,
            "redirect_uri": "http://localhost:5001/callback",
            "code_verifier": verifier,
        }
        r1 = client.post("/token", data=data)
        assert r1.status_code == 200
        r2 = client.post("/token", data=data)
        assert r2.status_code == 400
        assert r2.json()["detail"]["error"] == "invalid_grant"

    def test_wrong_code_verifier_rejected(self, client, ac_client, test_user, db_session, setup_db):
        """A bad PKCE verifier must fail even with a valid code."""
        code, _ = _issue_auth_code(db_session, ac_client, test_user)
        r = client.post("/token", data={
            "grant_type": "authorization_code",
            "client_id": "web-client",
            "client_secret": "web-secret",
            "code": code,
            "redirect_uri": "http://localhost:5001/callback",
            "code_verifier": "wrong-verifier",
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_grant"

    def test_missing_code_verifier_rejected(self, client, ac_client, test_user, db_session, setup_db):
        """Omitting code_verifier when PKCE was used must fail."""
        code, _ = _issue_auth_code(db_session, ac_client, test_user)
        r = client.post("/token", data={
            "grant_type": "authorization_code",
            "client_id": "web-client",
            "client_secret": "web-secret",
            "code": code,
            "redirect_uri": "http://localhost:5001/callback",
            # code_verifier deliberately omitted
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_request"

    def test_redirect_uri_mismatch_rejected(self, client, ac_client, test_user, db_session, setup_db):
        code, verifier = _issue_auth_code(db_session, ac_client, test_user)
        r = client.post("/token", data={
            "grant_type": "authorization_code",
            "client_id": "web-client",
            "client_secret": "web-secret",
            "code": code,
            "redirect_uri": "http://evil.example.com/callback",
            "code_verifier": verifier,
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "invalid_grant"


# ---------------------------------------------------------------------------
# Common auth errors
# ---------------------------------------------------------------------------

class TestAuthErrors:
    def test_invalid_client_secret_rejected(self, client, cc_client, setup_db):
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "svc-client",
            "client_secret": "wrong-secret",
        })
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "invalid_client"

    def test_unknown_client_id_rejected(self, client, setup_db):
        r = client.post("/token", data={
            "grant_type": "client_credentials",
            "client_id": "no-such-client",
            "client_secret": "anything",
        })
        assert r.status_code == 401
        assert r.json()["detail"]["error"] == "invalid_client"

    def test_wrong_grant_type_rejected(self, client, cc_client, setup_db):
        """Client registered for client_credentials must not use authorization_code."""
        r = client.post("/token", data={
            "grant_type": "authorization_code",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
            "code": "any",
            "redirect_uri": "http://localhost/cb",
        })
        assert r.status_code == 400
        assert r.json()["detail"]["error"] == "unauthorized_client"

    def test_unsupported_grant_type_rejected(self, client, cc_client, setup_db):
        r = client.post("/token", data={
            "grant_type": "password",
            "client_id": "svc-client",
            "client_secret": "svc-secret",
        })
        # password grant type is in the allowed_grant_types check, which passes
        # only if the client allows it — svc-client doesn't, so 400 unauthorized_client
        assert r.status_code == 400
