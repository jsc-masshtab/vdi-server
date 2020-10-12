"""Task add column message

Revision ID: 0f99d16903fd
Revises: 0b059b0d7d0c
Create Date: 2020-10-12 17:26:14.933926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f99d16903fd'
down_revision = '0b059b0d7d0c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task', sa.Column('message', sa.Unicode(length=256), nullable=True))
    op.alter_column(table_name='task', column_name='resume_on_app_startup', new_column_name='resumable')


def downgrade():
    op.drop_column('task', 'message')
    op.alter_column(table_name='task', column_name='resumable', new_column_name='resume_on_app_startup')
