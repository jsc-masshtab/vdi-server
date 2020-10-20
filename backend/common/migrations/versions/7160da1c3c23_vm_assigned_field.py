"""vm_assigned_field

Revision ID: 7160da1c3c23
Revises: fd0a9d655a9f
Create Date: 2020-10-01 15:08:34.458811

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7160da1c3c23'
down_revision = 'fd0a9d655a9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vm', sa.Column('assigned_to_user', sa.BOOLEAN(), nullable=True))
    op.execute("""update public.vm set broken = False""")
    op.alter_column('vm', 'assigned_to_user',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vm', 'assigned_to_user')
    # ### end Alembic commands ###