"""AuthenticationDirectory GUID for groups

Revision ID: 3bdd27d82159
Revises: b70e97b19709
Create Date: 2020-05-28 21:45:10.542313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bdd27d82159'
down_revision = 'b70e97b19709'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('authentication_directory', 'service_password',
                    existing_type=sa.VARCHAR(length=128),
                    type_=sa.Unicode(length=1000),
                    existing_nullable=True)
    op.add_column('group', sa.Column('ad_guid', sa.Unicode(length=36), nullable=True))
    op.create_unique_constraint(None, 'group', ['ad_guid'])


def downgrade():
    op.drop_constraint('group_ad_guid_key', 'group', type_='unique')
    op.drop_column('group', 'ad_guid')
    op.alter_column('authentication_directory', 'service_password',
                    existing_type=sa.Unicode(length=1000),
                    type_=sa.VARCHAR(length=128),
                    existing_nullable=True)
