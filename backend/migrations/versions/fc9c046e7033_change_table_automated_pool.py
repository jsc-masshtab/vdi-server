"""change_table_automated_pool_colunm_create_thin_clones

Revision ID: fc9c046e7033
Revises: fd8fe108d273
Create Date: 2019-12-02 11:37:34.454683

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fc9c046e7033'
down_revision = 'fd8fe108d273'
branch_labels = None
depends_on = None


def upgrade():
    default_value = True
    # add column
    op.add_column('automated_pool', sa.Column('create_thin_clones', sa.Boolean(), default=default_value))
    # # set initial values
    set_default_values_query = 'UPDATE automated_pool SET create_thin_clones = {}'.format(default_value)
    op.execute(set_default_values_query)
    # make column not nullable
    op.alter_column('automated_pool', 'create_thin_clones',
                    existing_type=sa.Boolean(),
                    nullable=False)


def downgrade():
    op.drop_column('automated_pool', 'create_thin_clones')
