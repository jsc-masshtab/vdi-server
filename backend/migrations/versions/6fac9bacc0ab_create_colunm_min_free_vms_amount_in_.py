"""create_colunm_min_free_vms_amount_in_automated_pool

Revision ID: 6fac9bacc0ab
Revises: 3842510e083b
Create Date: 2020-01-27 15:16:51.142847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fac9bacc0ab'
down_revision = '3842510e083b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('automated_pool', sa.Column('min_free_vms_amount', sa.Integer()))


def downgrade():
    op.drop_column('automated_pool', 'min_free_vms_amount')
