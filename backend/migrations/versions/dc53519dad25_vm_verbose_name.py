"""Vm verbose_name

Revision ID: dc53519dad25
Revises: a9317f9d2ca3
Create Date: 2020-01-15 15:29:09.894140

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc53519dad25'
down_revision = 'a9317f9d2ca3'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('vm_pool_id_key', 'vm', type_='unique')
    op.drop_constraint('pools_users_pool_id_key', 'pools_users', type_='unique')
    op.alter_column('pool', 'datapool_id',
                    existing_type=postgresql.UUID(),
                    nullable=False)
    op.add_column('vm', sa.Column('verbose_name', sa.Unicode(length=255), nullable=False))


def downgrade():
    op.create_unique_constraint('pools_users_pool_id_key', 'pools_users', ['pool_id'])
    op.create_unique_constraint('vm_pool_id_key', 'vm', ['pool_id'])
    op.drop_column('vm', 'verbose_name')
    op.alter_column('pool', 'datapool_id',
                    existing_type=postgresql.UUID(),
                    nullable=True)
