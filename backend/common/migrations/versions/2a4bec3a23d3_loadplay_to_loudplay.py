"""LOADPLAY to LOUDPLAY

Revision ID: 2a4bec3a23d3
Revises: 9f39f90cc36d
Create Date: 2022-06-20 17:27:44.946737

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2a4bec3a23d3'
down_revision = '9f39f90cc36d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE poolconnectiontypes RENAME VALUE 'LOADPLAY' TO 'LOUDPLAY';")


def downgrade():
    op.execute("ALTER TYPE poolconnectiontypes RENAME VALUE 'LOUDPLAY' TO 'LOADPLAY';")
