"""Add Repo.reindex_task_id

Revision ID: 9b71738fa3bd
Revises: 30a9e8657024
Create Date: 2025-11-12 15:39:15.652239

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b71738fa3bd"
down_revision: Union[str, None] = "30a9e8657024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repo", sa.Column("reindex_task_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("repo", "reindex_task_id")
