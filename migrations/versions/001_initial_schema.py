"""Initial schema: users, oauth_clients, authorization_codes, tokens

Revision ID: 001
Revises:
Create Date: 2026-05-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "oauth_clients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_id", sa.String(128), unique=True, nullable=False),
        sa.Column("client_secret_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("redirect_uris", sa.JSON, nullable=False),
        sa.Column("allowed_grant_types", sa.JSON, nullable=False),
        sa.Column("allowed_scopes", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_oauth_clients_client_id", "oauth_clients", ["client_id"])

    op.create_table(
        "authorization_codes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(255), unique=True, nullable=False),
        sa.Column("scope", sa.String(512), nullable=False, server_default=""),
        sa.Column("redirect_uri", sa.String(512), nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=True),
        sa.Column("code_challenge_method", sa.String(8), nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("oauth_clients.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_authorization_codes_code", "authorization_codes", ["code"])

    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("access_token", sa.Text, unique=True, nullable=False),
        # "user" for Authorization Code flow, "client" for Client Credentials flow
        sa.Column("token_type", sa.String(16), nullable=False),
        sa.Column("scope", sa.String(512), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        # NULL for client_credentials tokens — no user is involved
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("oauth_clients.id"), nullable=False),
    )
    op.create_index("ix_tokens_access_token", "tokens", ["access_token"])


def downgrade() -> None:
    op.drop_table("tokens", if_exists=True)
    op.drop_table("authorization_codes", if_exists=True)
    op.drop_table("oauth_clients", if_exists=True)
    op.drop_table("users", if_exists=True)
