"""Initial schema for reviews, review_issues, and pipeline_traces

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-19 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: reviews ───────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("repo_url", sa.String(), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviews_id"), "reviews", ["id"], unique=False)
    op.create_index(op.f("ix_reviews_pr_number"), "reviews", ["pr_number"], unique=False)
    op.create_index(op.f("ix_reviews_repo_url"), "reviews", ["repo_url"], unique=False)

    # ── Table: review_issues ─────────────────────────────────────
    op.create_table(
        "review_issues",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("review_id", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("issue_description", sa.String(), nullable=True),
        sa.Column("root_cause", sa.String(), nullable=True),
        sa.Column("trigger_condition", sa.String(), nullable=True),
        sa.Column("fix_suggestion", sa.String(), nullable=True),
        sa.Column("patch", sa.String(), nullable=True),
        sa.Column("issue_type", sa.String(), nullable=True),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reasoning_trace", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_issues_file_path"), "review_issues", ["file_path"], unique=False)
    op.create_index(op.f("ix_review_issues_id"), "review_issues", ["id"], unique=False)

    # ── Table: pipeline_traces ───────────────────────────────────
    op.create_table(
        "pipeline_traces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("review_id", sa.String(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_traces_id"), "pipeline_traces", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_traces_id"), table_name="pipeline_traces")
    op.drop_table("pipeline_traces")
    op.drop_index(op.f("ix_review_issues_id"), table_name="review_issues")
    op.drop_index(op.f("ix_review_issues_file_path"), table_name="review_issues")
    op.drop_table("review_issues")
    op.drop_index(op.f("ix_reviews_repo_url"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_pr_number"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_id"), table_name="reviews")
    op.drop_table("reviews")
