"""add block status_updated_at

A block's status now belongs to the week it was set in. Existing completed /
missed / skipped blocks take the time of their latest execution log; ones with
no log (e.g. skipped) get NULL and read as PLANNED from now on.

Revision ID: b7e4d2a9c1f3
Revises: 9f1a2c4d5e6b
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e4d2a9c1f3'
down_revision: Union[str, Sequence[str], None] = '9f1a2c4d5e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scheduled_blocks', sa.Column('status_updated_at', sa.DateTime(), nullable=True))
    op.execute(
        """
        UPDATE scheduled_blocks
        SET status_updated_at = (
            SELECT MAX(logged_at) FROM execution_logs
            WHERE execution_logs.block_id = scheduled_blocks.id
        )
        WHERE status != 'PLANNED'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scheduled_blocks', 'status_updated_at')
