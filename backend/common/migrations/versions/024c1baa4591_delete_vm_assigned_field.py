"""delete_vm_assigned_field

Revision ID: 024c1baa4591
Revises: 2ae1d06f2141
Create Date: 2020-11-05 18:52:02.366785

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '024c1baa4591'
down_revision = '2ae1d06f2141'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("update vm set status = 'SERVICE' where assigned_to_user is true")
    op.drop_column('vm', 'assigned_to_user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vm', sa.Column('assigned_to_user', sa.BOOLEAN(), nullable=True))
    op.execute("""update public.vm set assigned_to_user = False""")
    op.alter_column('vm', 'assigned_to_user',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    # ### end Alembic commands ###
