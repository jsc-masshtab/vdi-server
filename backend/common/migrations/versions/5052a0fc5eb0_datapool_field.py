"""Datapool_field.

Revision ID: 5052a0fc5eb0
Revises: ba1b6817b510
Create Date: 2021-10-11 16:43:58.261628

"""
from alembic import op

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5052a0fc5eb0"
down_revision = "cbdd458222a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pool", sa.Column("datapool_id", postgresql.UUID(), nullable=True))


def downgrade():
    op.drop_column("pool", "datapool_id")
