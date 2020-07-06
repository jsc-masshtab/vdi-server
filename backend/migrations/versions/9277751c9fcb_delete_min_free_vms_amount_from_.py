"""delete_min_free_vms_amount_from_automated_pool

Revision ID: 9277751c9fcb
Revises: 03c207dae231
Create Date: 2020-06-26 16:47:42.518797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9277751c9fcb'
down_revision = '03c207dae231'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # drop column
    op.drop_column('automated_pool', 'min_free_vms_amount')
    # set increase_step to 1 for existing pools
    op.execute('UPDATE automated_pool SET increase_step = 1')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('automated_pool', sa.Column('min_free_vms_amount', sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE automated_pool SET min_free_vms_amount = 1")
    op.alter_column('automated_pool', 'min_free_vms_amount', nullable=False)
    # ### end Alembic commands ###
