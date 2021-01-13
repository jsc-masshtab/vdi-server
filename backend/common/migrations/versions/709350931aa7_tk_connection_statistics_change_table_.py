"""tk_connection_statistics_change_table_name

Revision ID: 709350931aa7
Revises: a6f0e86cff98
Create Date: 2020-12-21 14:51:36.190078

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '709350931aa7'
down_revision = 'a6f0e86cff98'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table(old_table_name='tk_connection_statistis', new_table_name='tk_connection_statistics')


def downgrade():
    op.rename_table(old_table_name='tk_connection_statistics', new_table_name='tk_connection_statistis')
