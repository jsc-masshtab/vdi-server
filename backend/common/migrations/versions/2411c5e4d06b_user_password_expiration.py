"""user password expiration

Revision ID: 2411c5e4d06b
Revises: a8104fe81f12
Create Date: 2022-10-11 19:48:27.584312

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2411c5e4d06b'
down_revision = 'a8104fe81f12'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('password_expiration')
    op.create_unique_constraint(None, 'rds_pool', ['id'])
    op.add_column('user', sa.Column('password_expiration_date', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('user', 'password_expiration_date')
    op.create_table('password_expiration',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('expiration_date', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='password_expiration_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='password_expiration_pkey')
    )
