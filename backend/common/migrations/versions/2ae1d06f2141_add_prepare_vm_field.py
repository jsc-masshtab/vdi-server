"""add_prepare_vm_field

Revision ID: 2ae1d06f2141
Revises: 004d0c8a20aa
Create Date: 2020-11-03 14:47:40.177415

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2ae1d06f2141'
down_revision = '004d0c8a20aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('automated_pool', sa.Column('prepare_vms', sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set prepare_vms = True""")
    op.alter_column('automated_pool', 'prepare_vms',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('automated_pool', 'prepare_vms')
    # ### end Alembic commands ###
