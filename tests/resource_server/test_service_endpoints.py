"""Tests for the machine API endpoint (/api/service/stats).

Verifies that require_client_token correctly allows client tokens,
rejects user tokens, and rejects missing/invalid tokens.
Also cross-checks that user endpoints reject client tokens.
"""
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parents[2]
AUTH = ROOT / "auth-server"
RS   = ROOT / "resource-server"


def _load(path: Path, sys_name: str) -> object:
    """Load a module from an explicit path and register it in sys.modules."""
    spec = importlib.util.spec_from_file_location(sys_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[sys_name] = mod
    spec.loader.exec_module(mod)
    return mod


# auth_security does `from config import ...` at load time, so auth-server's
# config must be registered as 'config' before auth_security is loaded.
# We then overwrite 'config' with the resource-server's config so the RS
# modules pick up the right values when they load.
_load(AUTH / "config.py", "auth_config")
_load(AUTH / "config.py", "config")          # satisfies auth_security's import
auth_sec = _load(AUTH / "security.py", "auth_security")

# Now overwrite 'config' so all resource-server imports get RS config.
_load(RS / "config.py",   "config")
_load(RS / "security.py", "security")
_load(RS / "routes.py",   "routes")
rs_main = _load(RS / "main.py", "main")


@pytest.fixture(scope="module")
def client():
    return TestClient(rs_main.app)


@pytest.fixture(scope="module")
def user_token():
    return auth_sec.create_user_token(user_id=1, scope="read write")


@pytest.fixture(scope="module")
def client_token():
    return auth_sec.create_client_token(client_id="service-client", scope="read:stats")


# ---------------------------------------------------------------------------
# /api/service/stats
# ---------------------------------------------------------------------------

class TestServiceStats:
    def test_client_token_allowed(self, client, client_token):
        r = client.get("/api/service/stats", headers={"Authorization": f"Bearer {client_token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["requested_by"] == "service-client"
        assert "stats" in body

    def test_user_token_rejected(self, client, user_token):
        """User tokens must not access machine endpoints."""
        r = client.get("/api/service/stats", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403
        assert r.json()["detail"]["error"] == "insufficient_scope"

    def test_no_token_rejected(self, client):
        r = client.get("/api/service/stats")
        assert r.status_code == 401

    def test_invalid_token_rejected(self, client):
        r = client.get("/api/service/stats", headers={"Authorization": "Bearer not.a.token"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# /api/user/profile — cross-check that client tokens are rejected
# ---------------------------------------------------------------------------

class TestUserProfile:
    def test_user_token_allowed(self, client, user_token):
        r = client.get("/api/user/profile", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        assert r.json()["token_type"] == "user"

    def test_client_token_rejected(self, client, client_token):
        """Client tokens must not access user endpoints."""
        r = client.get("/api/user/profile", headers={"Authorization": f"Bearer {client_token}"})
        assert r.status_code == 403
        assert r.json()["detail"]["error"] == "insufficient_scope"


# ---------------------------------------------------------------------------
# /health — no auth required
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
