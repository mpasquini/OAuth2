"""Seed the database with test users and OAuth2 clients.

Run once after `make migrate` (or `alembic upgrade head`):

    python scripts/seed.py

Environment variables read (with defaults for local dev):
    DATABASE_URL          sqlite:///./auth-server/oauth2.db
    SERVICE_CLIENT_ID     service-client
    SERVICE_CLIENT_SECRET service-client-secret
    SERVICE_CLIENT_SCOPES read:stats
"""

import os
import sys
from pathlib import Path

# Allow importing from auth-server without installing the package.
# Local dev: script lives at repo/scripts/seed.py → auth-server is at repo/auth-server/
# Docker:    script is COPYed to /app/scripts/seed.py and auth-server files are COPYed
#            directly to /app/ (not /app/auth-server/), so fall back to the parent dir.
AUTH_SERVER = Path(__file__).parent.parent / "auth-server"
if not AUTH_SERVER.is_dir():
    AUTH_SERVER = Path(__file__).parent.parent
sys.path.insert(0, str(AUTH_SERVER))

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import AuthorizationCode, Base, OAuthClient, Token, User

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth-server/oauth2.db")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)


def _hash(value: str) -> str:
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()


def _seed_users(db: Session) -> None:
    users = [
        {"username": "alice", "email": "alice@example.com", "password": "alice-password", "is_admin": True},
        {"username": "bob",   "email": "bob@example.com",   "password": "bob-password",   "is_admin": False},
        {"username": "charlie", "email": "charlie@example.com", "password": "charlie-password", "is_admin": False},
    ]
    for u in users:
        if db.query(User).filter(User.username == u["username"]).first():
            print(f"  user '{u['username']}' already exists — skipped")
            continue
        db.add(User(
            username=u["username"],
            email=u["email"],
            password_hash=_hash(u["password"]),
            is_admin=u["is_admin"],
        ))
        print(f"  created user '{u['username']}'")


def _seed_clients(db: Session) -> None:
    clients = [
        {
            "client_id": os.getenv("OAUTH2_CLIENT_ID", "web-client"),
            "client_secret": os.getenv("OAUTH2_CLIENT_SECRET", "web-client-secret"),
            "name": "Web Client (Authorization Code + PKCE)",
            "redirect_uris": [os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:5001/callback")],
            "allowed_grant_types": ["authorization_code"],
            "allowed_scopes": ["read", "write", "profile"],
        },
        {
            "client_id": os.getenv("SERVICE_CLIENT_ID", "service-client"),
            "client_secret": os.getenv("SERVICE_CLIENT_SECRET", "service-client-secret"),
            "name": "Service Client (Client Credentials)",
            "redirect_uris": [],
            "allowed_grant_types": ["client_credentials"],
            "allowed_scopes": os.getenv("SERVICE_CLIENT_SCOPES", "read:stats").split(),
        },
    ]
    for c in clients:
        if db.query(OAuthClient).filter(OAuthClient.client_id == c["client_id"]).first():
            print(f"  client '{c['client_id']}' already exists — skipped")
            continue
        db.add(OAuthClient(
            client_id=c["client_id"],
            client_secret_hash=_hash(c["client_secret"]),
            name=c["name"],
            redirect_uris=c["redirect_uris"],
            allowed_grant_types=c["allowed_grant_types"],
            allowed_scopes=c["allowed_scopes"],
        ))
        print(f"  created client '{c['client_id']}' (grant_types={c['allowed_grant_types']})")


def main() -> None:
    print(f"Database: {DATABASE_URL}")
    Base.metadata.create_all(engine)  # no-op if tables already exist

    with Session(engine) as db:
        print("\nSeeding users...")
        _seed_users(db)

        print("\nSeeding OAuth2 clients...")
        _seed_clients(db)

        db.commit()

    print("\nDone.")


if __name__ == "__main__":
    main()
