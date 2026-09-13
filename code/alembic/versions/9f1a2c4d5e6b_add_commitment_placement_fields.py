"""add commitment placement fields

Revision ID: 9f1a2c4d5e6b
Revises: 07d43590c27a
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f1a2c4d5e6b'
down_revision: Union[str, Sequence[str], None] = '07d43590c27a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DAY_ENUM = sa.Enum(
    'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
    name='dayofweek',
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('commitments', sa.Column('day', _DAY_ENUM, nullable=True))
    op.add_column('commitments', sa.Column('slot_index', sa.Integer(), nullable=True))
    op.add_column('commitments', sa.Column('deadline_day', _DAY_ENUM, nullable=True))
    op.add_column('commitments', sa.Column('deadline_slot', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('commitments', 'deadline_slot')
    op.drop_column('commitments', 'deadline_day')
    op.drop_column('commitments', 'slot_index')
    op.drop_column('commitments', 'day')
