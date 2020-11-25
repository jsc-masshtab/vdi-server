"""AD schema updates

Revision ID: 8bfcd92f81c4
Revises: 063f3ac2641c
Create Date: 2020-11-25 09:01:20.960889

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8bfcd92f81c4'
down_revision = '063f3ac2641c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('authentication_directory', sa.Column('dc_str', sa.Unicode(length=255), nullable=True))
    op.create_unique_constraint(None, 'authentication_directory', ['dc_str'])
    op.drop_column('authentication_directory', 'admin_server')
    op.drop_column('authentication_directory', 'subdomain_name')
    op.drop_column('authentication_directory', 'kdc_urls')
    op.drop_column('authentication_directory', 'sso')
    op.execute('''update public.authentication_directory set dc_str = domain_name;''')
    op.alter_column('authentication_directory', 'dc_str',
                    existing_type=sa.Unicode(length=255),
                    nullable=False)


def downgrade():
    op.add_column('authentication_directory', sa.Column('sso', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('authentication_directory',
                  sa.Column('kdc_urls', postgresql.ARRAY(sa.VARCHAR(length=255)), autoincrement=False, nullable=True))
    op.add_column('authentication_directory',
                  sa.Column('subdomain_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('authentication_directory',
                  sa.Column('admin_server', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.drop_column('authentication_directory', 'dc_str')
