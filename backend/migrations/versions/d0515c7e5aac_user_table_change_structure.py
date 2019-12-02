"""user table change structure

Revision ID: d0515c7e5aac
Revises: 27386d7871d2
Create Date: 2019-11-18 16:17:36.331332

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd0515c7e5aac'
down_revision = 'f7a3e4780221'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('drop table pools_users cascade;')
    op.create_table('pools_users',
    sa.Column('pool_id', postgresql.UUID(), nullable=True),
    sa.Column('user_id', postgresql.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['pool_id'], ['pool.pool_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )


def downgrade():
    op.create_table('pools_users',
    sa.Column('pool_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['pool_id'], ['pool.pool_id'], name='pools_users_pool_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='pools_users_user_id_fkey')
    )
