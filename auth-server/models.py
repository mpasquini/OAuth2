from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    authorization_codes = relationship("AuthorizationCode", back_populates="user", cascade="all, delete-orphan")


class OAuthClient(Base):
    """A registered OAuth2 client application.

    allowed_grant_types controls which flows this client may use:
      - "authorization_code"  → browser-based user flow (Client App)
      - "client_credentials"  → machine-to-machine flow (Service Client)
    allowed_scopes restricts which scopes this client may request.
    """

    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True)
    client_id = Column(String(128), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    # List of allowed redirect URIs (Authorization Code flow only).
    redirect_uris = Column(JSON, nullable=False, default=list)

    # e.g. ["authorization_code"] or ["client_credentials"]
    allowed_grant_types = Column(JSON, nullable=False, default=list)

    # e.g. ["read", "write"] or ["read:stats"]
    allowed_scopes = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    tokens = relationship("Token", back_populates="client", cascade="all, delete-orphan")
    authorization_codes = relationship("AuthorizationCode", back_populates="client", cascade="all, delete-orphan")

    def allows_grant_type(self, grant_type: str) -> bool:
        return grant_type in (self.allowed_grant_types or [])

    def allows_scope(self, scope: str) -> bool:
        requested = set(scope.split())
        return requested.issubset(set(self.allowed_scopes or []))


class AuthorizationCode(Base):
    """Short-lived code issued at /authorize, exchanged for a token at /token.
    Only used in the Authorization Code flow.
    """

    __tablename__ = "authorization_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(255), unique=True, nullable=False, index=True)
    scope = Column(String(512), nullable=False, default="")
    redirect_uri = Column(String(512), nullable=False)
    # PKCE fields
    code_challenge = Column(String(128), nullable=True)
    code_challenge_method = Column(String(8), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    client_id = Column(Integer, ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    client = relationship("OAuthClient", back_populates="authorization_codes")
    user = relationship("User", back_populates="authorization_codes")


class Token(Base):
    """Issued access token.

    user_id is NULL for client_credentials tokens — the token belongs to the
    client itself, not a user. Check token_type to tell them apart:
      - "user"   → Authorization Code flow; user_id is set
      - "client" → Client Credentials flow; user_id is NULL
    """

    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    access_token = Column(Text, unique=True, nullable=False, index=True)
    token_type = Column(String(16), nullable=False)  # "user" | "client"
    scope = Column(String(512), nullable=False, default="")
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # NULL for client_credentials tokens
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("oauth_clients.id"), nullable=False)

    user = relationship("User", back_populates="tokens")
    client = relationship("OAuthClient", back_populates="tokens")
