"""Default controller

Revision ID: 747034e9b106
Revises: f6da15d7a43d
Create Date: 2019-10-31 16:05:06.780419

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '747034e9b106'
down_revision = 'f6da15d7a43d'
branch_labels = None
depends_on = None


def upgrade():
    insert_controller_query = """insert into controller("id", "verbose_name", "status", "address", "description", 
    "username", "password", "ldap_connection") values ('621a162e-0176-4e92-98fb-e552f6b9bc57', 'Remote controller', 
    'ACTIVE', '192.168.7.250', 'Remote controller', 'vdi', '4ever', false);"""
    op.execute(insert_controller_query)


def downgrade():
    op.execute('truncate table controller cascade;')
