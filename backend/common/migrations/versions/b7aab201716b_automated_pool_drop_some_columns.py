"""automated_pool_drop_some_columns

Revision ID: b7aab201716b
Revises: 1b23d22179d7
Create Date: 2020-10-19 15:41:00.496561

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7aab201716b'
down_revision = '1b23d22179d7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('automated_pool', 'min_size')
    op.drop_column('automated_pool', 'max_size')
    op.drop_column('automated_pool', 'max_vm_amount')


def downgrade():
    op.add_column('automated_pool', sa.Column('min_size', sa.Integer(), nullable=True))
    op.add_column('automated_pool', sa.Column('max_size', sa.Integer(), nullable=True))
    op.add_column('automated_pool', sa.Column('max_vm_amount', sa.Integer(), nullable=True))

    op.execute("""UPDATE public.automated_pool SET min_size =1""")
    op.execute("""UPDATE public.automated_pool SET max_size =1000""")
    op.execute("""UPDATE public.automated_pool SET max_vm_amount =1000""")

    op.alter_column('automated_pool', 'min_size', existing_type=sa.Integer(), nullable=False)
    op.alter_column('automated_pool', 'max_size', existing_type=sa.Integer(), nullable=False)
    op.alter_column('automated_pool', 'max_vm_amount', existing_type=sa.Integer(), nullable=False)
