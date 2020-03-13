"""empty message

Revision ID: 8aebac9a4baf
Revises: 24e40621a8f8
Create Date: 2020-03-09 11:19:03.086832

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8aebac9a4baf'
down_revision = '24e40621a8f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('vm_user_id_fkey', 'vm', type_='foreignkey')
    op.drop_column('vm', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vm', sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('vm_user_id_fkey', 'vm', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###