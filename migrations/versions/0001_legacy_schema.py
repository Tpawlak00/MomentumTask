"""Baseline matching the original init.sql (stamp only for existing databases)."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("serial_num", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("is_borrowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("borrowed_by", sa.Integer(), nullable=True),
        sa.Column("borrowed_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("books")
