"""Task column progress

Revision ID: 0b059b0d7d0c
Revises: 2e402a48baca
Create Date: 2020-10-08 13:48:10.045208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b059b0d7d0c'
down_revision = '2e402a48baca'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task', sa.Column('progress', sa.Integer(), nullable=False))


def downgrade():
    op.drop_column('task', 'progress')
