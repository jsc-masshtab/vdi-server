"""Password history

Revision ID: e334e64d4c2c
Revises: 4877bb8b4f29
Create Date: 2022-10-05 17:00:08.021734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e334e64d4c2c'
down_revision = 'e515cfece1bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('password_history',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('user_id', postgresql.UUID(), nullable=False),
    sa.Column('password', sa.Unicode(length=128), nullable=False),
    sa.Column('changed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('password_history')
