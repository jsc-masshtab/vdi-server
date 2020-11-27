"""add_table_active_tk_connection

Revision ID: 40932ab2f84c
Revises: 8bfcd92f81c4
Create Date: 2020-11-25 16:09:36.049521

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '40932ab2f84c'
down_revision = '8bfcd92f81c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('active_tk_connection',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('veil_connect_version', sa.Unicode(length=128)),
                    sa.Column('vm_id', postgresql.UUID()),
                    sa.Column('tk_ip', sa.Unicode(length=128)),
                    sa.Column('tk_os', sa.Unicode(length=128)),
                    sa.Column('connected', sa.DateTime(timezone=True), nullable=False,
                              server_default=sa.text('now()')),
                    sa.Column('data_received', sa.DateTime(timezone=True), nullable=False,
                              server_default=sa.text('now()')),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('user_id'),
                    )


def downgrade():
    op.drop_table('active_tk_connection')
