"""Password expiration

Revision ID: a8104fe81f12
Revises: e334e64d4c2c
Create Date: 2022-10-07 17:02:36.465302

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a8104fe81f12'
down_revision = 'e334e64d4c2c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('password_expiration',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('user_id', postgresql.UUID(), nullable=False),
    sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('password_expiration')

