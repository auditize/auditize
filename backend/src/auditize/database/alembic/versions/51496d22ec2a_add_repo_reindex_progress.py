"""Add Repo reindex progress

Revision ID: 51496d22ec2a
Revises: 30a9e8657024
Create Date: 2025-12-02 11:11:40.943419

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "51496d22ec2a"
down_revision: Union[str, None] = "30a9e8657024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repo", sa.Column("reindex_cursor", sa.String(), nullable=True))
    op.add_column(
        "repo",
        sa.Column(
            "reindexed_logs_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    op.drop_column("repo", "reindexed_logs_count")
    op.drop_column("repo", "reindex_cursor")
