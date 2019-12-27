"""Controller status type

Revision ID: f98afc49eec9
Revises: 20e197310113
Create Date: 2019-12-17 17:40:26.943341

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f98afc49eec9'
down_revision = '20e197310113'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('controller', 'status')
    op.add_column('controller', sa.Column('status', sa.Enum('CREATING', 'ACTIVE', 'FAILED', 'DELETING',
                                                            'SERVICE', 'PARTIAL', 'BAD_AUTH', name='status'),
                                          autoincrement=False, nullable=False, server_default='ACTIVE'))


def downgrade():
    op.drop_column('controller', 'status')
    op.add_column('controller', sa.Column('status', sa.Unicode(length=128), nullable=True))
