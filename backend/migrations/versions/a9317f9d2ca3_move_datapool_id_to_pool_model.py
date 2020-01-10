"""move_datapool_id_to_pool_model

Revision ID: a9317f9d2ca3
Revises: f98afc49eec9
Create Date: 2020-01-09 14:12:37.531464

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a9317f9d2ca3'
down_revision = 'f98afc49eec9'
branch_labels = None
depends_on = None


def upgrade():
    pass
    op.drop_column('automated_pool', 'datapool_id')
    op.add_column('pool', sa.Column('datapool_id', postgresql.UUID(), nullable=True))


def downgrade():
    op.drop_column('pool', 'datapool_id')
    op.add_column('automated_pool', sa.Column('datapool_id', postgresql.UUID(), nullable=True))