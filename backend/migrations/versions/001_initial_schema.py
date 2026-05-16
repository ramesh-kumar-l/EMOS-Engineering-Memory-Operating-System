"""Initial schema: memory_documents table + FTS5 virtual table

Revision ID: 001
Revises: None
Create Date: 2026-05-15
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
        "memory_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("tags", sa.JSON, nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("word_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_indexed", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_documents_slug", "memory_documents", ["slug"])
    op.create_index("ix_memory_documents_category", "memory_documents", ["category"])

    # FTS5 virtual tables are not tracked by Alembic — raw SQL only
    op.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts "
        "USING fts5(slug UNINDEXED, title, content, tokenize='porter ascii')"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_fts")
    op.drop_table("memory_documents")
