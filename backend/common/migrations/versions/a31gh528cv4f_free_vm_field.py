"""free_vm_field.

Revision ID: a31gh528cv4f
Revises: 73cb8be45669
Create Date: 2021-11-23 12:35:23.141143

"""
from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a31gh528cv4f"
down_revision = "73cb8be45669"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pool", sa.Column("free_vm_from_user", sa.Boolean(), nullable=True))
    op.execute("""update public.pool set free_vm_from_user = False""")
    op.alter_column("pool", "free_vm_from_user", existing_type=sa.BOOLEAN(), nullable=False)


def downgrade():
    op.drop_column("pool", "free_vm_from_user")
