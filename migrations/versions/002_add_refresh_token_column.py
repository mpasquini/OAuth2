"""Add refresh_token column to tokens table

Revision ID: 002
Revises: 001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tokens", sa.Column("refresh_token", sa.Text, nullable=True))
    op.create_index("ix_tokens_refresh_token", "tokens", ["refresh_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tokens_refresh_token", table_name="tokens")
    op.drop_column("tokens", "refresh_token")
