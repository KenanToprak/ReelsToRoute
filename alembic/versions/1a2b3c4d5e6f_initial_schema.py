"""Initial schema for users, routes, and locations

Revision ID: 1a2b3c4d5e6f
Revises:
Create Date: 2026-09-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial users, routes, and locations tables."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_full_name', 'users', ['full_name'], unique=False)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    op.create_table(
        'routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_routes_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_routes'),
    )
    op.create_index('ix_routes_id', 'routes', ['id'], unique=False)
    op.create_index('ix_routes_user_id', 'routes', ['user_id'], unique=False)

    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('source_image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], name='fk_locations_route_id_routes'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_locations_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_locations'),
    )
    op.create_index('ix_locations_id', 'locations', ['id'], unique=False)
    op.create_index('ix_locations_latitude', 'locations', ['latitude'], unique=False)
    op.create_index('ix_locations_longitude', 'locations', ['longitude'], unique=False)
    op.create_index('ix_locations_route_id', 'locations', ['route_id'], unique=False)
    op.create_index('ix_locations_user_id', 'locations', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop locations, routes, and users tables."""
    op.drop_index('ix_locations_user_id', table_name='locations')
    op.drop_index('ix_locations_route_id', table_name='locations')
    op.drop_index('ix_locations_longitude', table_name='locations')
    op.drop_index('ix_locations_latitude', table_name='locations')
    op.drop_index('ix_locations_id', table_name='locations')
    op.drop_table('locations')

    op.drop_index('ix_routes_user_id', table_name='routes')
    op.drop_index('ix_routes_id', table_name='routes')
    op.drop_table('routes')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_full_name', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
