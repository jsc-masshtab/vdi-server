"""add_sso_field_for_auth_dir.

Revision ID: a76ge5d8oo2f
Revises: 9d14f7f75d65
Create Date: 2021-12-22 14:13:23.131024

"""
from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a76ge5d8oo2f"
down_revision = "9d14f7f75d65"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("authentication_directory", sa.Column("sso", sa.Boolean(), nullable=True))
    op.execute("""update public.authentication_directory set sso = False""")
    op.alter_column("authentication_directory", "sso", existing_type=sa.BOOLEAN(), nullable=False)


def downgrade():
    op.drop_column("authentication_directory", "sso")
