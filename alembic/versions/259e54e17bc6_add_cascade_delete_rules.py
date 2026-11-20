"""Add cascade delete rules

Revision ID: 259e54e17bc6
Revises: 26545243bb2c
Create Date: 2026-09-04 14:09:27.679756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '259e54e17bc6'
down_revision: Union[str, Sequence[str], None] = '26545243bb2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('locations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_locations_route_id_routes', type_='foreignkey')
        batch_op.drop_constraint('fk_locations_user_id_users', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_locations_user_id_users', 'users', ['user_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_locations_route_id_routes', 'routes', ['route_id'], ['id'], ondelete='SET NULL'
        )

    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_routes_user_id_users', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_routes_user_id_users', 'users', ['user_id'], ['id'], ondelete='CASCADE'
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_routes_user_id_users', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_routes_user_id_users', 'users', ['user_id'], ['id']
        )

    with op.batch_alter_table('locations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_locations_route_id_routes', type_='foreignkey')
        batch_op.drop_constraint('fk_locations_user_id_users', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_locations_user_id_users', 'users', ['user_id'], ['id']
        )
        batch_op.create_foreign_key(
            'fk_locations_route_id_routes', 'routes', ['route_id'], ['id']
        )
