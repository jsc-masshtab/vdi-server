"""connection_time_for_guest.

Revision ID: 6d4gr26hpv7a
Revises: 836f611f1cab
Create Date: 2021-10-06 12:45:32.361311

"""
from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6d4gr26hpv7a"
down_revision = "836f611f1cab"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("automated_pool", sa.Column("waiting_time", sa.Integer(), nullable=True))
    op.execute("""update public.automated_pool set waiting_time = 60 where is_guest = True""")


def downgrade():
    op.drop_column("automated_pool", "waiting_time")
