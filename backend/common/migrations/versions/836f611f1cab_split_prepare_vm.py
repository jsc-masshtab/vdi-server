"""split prepare vm in pool.

Revision ID: 836f611f1cab
Revises: 90d353c9e3f7
Create Date: 2021-09-15 14:34:05.341231

"""
from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "836f611f1cab"
down_revision = "90d353c9e3f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("automated_pool", sa.Column("enable_vms_remote_access", sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set enable_vms_remote_access = False""")
    op.execute("""update public.automated_pool set enable_vms_remote_access = True where prepare_vms = True""")
    op.alter_column("automated_pool", "enable_vms_remote_access", existing_type=sa.BOOLEAN(), nullable=False)

    op.add_column("automated_pool", sa.Column("start_vms", sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set start_vms = False""")
    op.execute("""update public.automated_pool set start_vms = True where prepare_vms = True""")
    op.alter_column("automated_pool", "start_vms", existing_type=sa.BOOLEAN(), nullable=False)

    op.add_column("automated_pool", sa.Column("set_vms_hostnames", sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set set_vms_hostnames = False""")
    op.execute("""update public.automated_pool set set_vms_hostnames = True where prepare_vms = True""")
    op.alter_column("automated_pool", "set_vms_hostnames", existing_type=sa.BOOLEAN(), nullable=False)

    op.add_column("automated_pool", sa.Column("include_vms_in_ad", sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set include_vms_in_ad = False""")
    op.execute("""update public.automated_pool set include_vms_in_ad = True where prepare_vms = True""")
    op.alter_column("automated_pool", "include_vms_in_ad", existing_type=sa.BOOLEAN(), nullable=False)

    op.drop_column("automated_pool", "prepare_vms")


def downgrade():
    op.add_column("automated_pool", sa.Column("prepare_vms", sa.Boolean(), nullable=True))
    op.execute("""update public.automated_pool set prepare_vms = False""")
    op.execute("""update public.automated_pool set prepare_vms = True where set_vms_hostnames = True""")
    op.alter_column("automated_pool", "prepare_vms", existing_type=sa.BOOLEAN(), nullable=False)

    op.drop_column("automated_pool", "enable_vms_remote_access")
    op.drop_column("automated_pool", "start_vms")
    op.drop_column("automated_pool", "set_vms_hostnames")
    op.drop_column("automated_pool", "include_vms_in_ad")
