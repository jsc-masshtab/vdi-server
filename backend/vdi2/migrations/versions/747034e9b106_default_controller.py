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
    'ACTIVE', '192.168.7.250', 'Remote controller', 'admin', 
    'gAAAAABdvCqNVz4ZhwNRVE9Xgh8iKYkfL4o2d7hlyW6ZdJbRa-Stwqp96p_5GEOlkpznHjeOxPhXt2RnvKItBWIXau3kbW2efQ==', false);"""
    op.execute(insert_controller_query)
    insert_user_query = """insert into public."user" values ('f9599771-cc95-45e4-9ae5-c8177b796aff', 'admin', 
    'pbkdf2_sha256$180000$4rVwLcWNf2op8PM4IhwkcsYluOYobsmNQNFZpIEK1TNvF4Bs1X$dUQihzANJkiYOCnXvN47XsVZGV5KECpMJrLGN43EnAs=',
     'admin@admin.admin', null, null,null, null, null, true, True);"""
    op.execute(insert_user_query)


def downgrade():
    op.execute('truncate table controller cascade;')
    op.execute('truncate table public."user" cascade;')
