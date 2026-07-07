"""seed user groups

Revision ID: a1b2c3d4e5f6
Revises: fedcdd07cdd0
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fedcdd07cdd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Seed the default user groups the app relies on at registration.
    # Idempotent: safe to run on databases that already have them.
    op.execute(
        "INSERT INTO users_groups (name) "
        "VALUES ('USER'), ('MODERATOR'), ('ADMIN') "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users_groups "
        "WHERE name IN ('USER', 'MODERATOR', 'ADMIN')"
    )
