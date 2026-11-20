"""Add estimated_days to Route

Revision ID: 26545243bb2c
Revises: 1a2b3c4d5e6f
Create Date: 2026-09-03 12:42:52.756952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26545243bb2c'
down_revision: Union[str, Sequence[str], None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('estimated_days', sa.Integer(), nullable=False, server_default='1')
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.drop_column('estimated_days')
