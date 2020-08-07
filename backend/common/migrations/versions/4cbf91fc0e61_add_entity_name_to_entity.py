"""add entity_name to entity

Revision ID: 4cbf91fc0e61
Revises: 97640ee31d01
Create Date: 2020-08-07 10:45:50.931162

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cbf91fc0e61'
down_revision = '97640ee31d01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('entity', sa.Column('entity_name', sa.Unicode(length=64), nullable=True))


def downgrade():
    op.drop_column('entity', 'entity_name')
