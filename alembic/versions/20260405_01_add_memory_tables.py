"""add memory tables

Revision ID: 20260405_01
Revises:
Create Date: 2026-04-05 17:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260405_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bot_users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', coalesce(content, ''))", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role in ('user', 'assistant', 'system')", name="ck_message_role"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["bot_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_messages_user_created_at",
        "conversation_messages",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_content_tsv",
        "conversation_messages",
        ["content_tsv"],
        unique=False,
        postgresql_using="gin",
    )

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("max_message_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["bot_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_summaries_user_created_at",
        "conversation_summaries",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_summaries_user_created_at",
        table_name="conversation_summaries",
    )
    op.drop_table("conversation_summaries")

    op.drop_index(
        "ix_conversation_messages_content_tsv",
        table_name="conversation_messages",
    )
    op.drop_index(
        "ix_conversation_messages_user_created_at",
        table_name="conversation_messages",
    )
    op.drop_table("conversation_messages")

    op.drop_table("bot_users")
