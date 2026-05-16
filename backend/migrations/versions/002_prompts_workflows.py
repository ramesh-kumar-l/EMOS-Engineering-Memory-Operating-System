"""Add prompt_templates, prompt_usages, workflow_runs, workflow_step_records

Revision ID: 002
Revises: 001
Create Date: 2026-05-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("template_body", sa.Text, nullable=False),
        sa.Column("parameters", sa.JSON, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_templates_slug", "prompt_templates", ["slug"])
    op.create_index("ix_prompt_templates_category", "prompt_templates", ["category"])

    op.create_table(
        "prompt_usages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_slug", sa.String(255), nullable=False),
        sa.Column("rendered_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("parameters_used", sa.JSON, nullable=False),
        sa.Column("workflow_run_id", sa.String(36), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_usages_template_slug", "prompt_usages", ["template_slug"])

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="in_progress"),
        sa.Column("current_step_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("context_data", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_runs_workflow_id", "workflow_runs", ["workflow_id"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])

    op.create_table(
        "workflow_step_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("step_index", sa.Integer, nullable=False),
        sa.Column("step_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_step_records_run_id", "workflow_step_records", ["run_id"])


def downgrade() -> None:
    op.drop_table("workflow_step_records")
    op.drop_table("workflow_runs")
    op.drop_table("prompt_usages")
    op.drop_table("prompt_templates")
