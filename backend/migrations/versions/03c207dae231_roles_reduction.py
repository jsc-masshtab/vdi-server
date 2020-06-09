"""Roles reduction

Revision ID: 03c207dae231
Revises: 3bdd27d82159
Create Date: 2020-06-08 15:27:50.515578

Существующие права из перечня 'READ_ONLY', 'VM_ADMINISTRATOR', 'NETWORK_ADMINISTRATOR', 'STORAGE_ADMINISTRATOR'
будут заменены на роль ADMINISTRATOR.
"""
from alembic import op
# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03c207dae231'
down_revision = '3bdd27d82159'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE role_types AS ENUM ('ADMINISTRATOR', 'SECURITY_ADMINISTRATOR', 'OPERATOR');")
    op.execute("UPDATE public.user_role SET role = 'ADMINISTRATOR' WHERE role IN ('READ_ONLY', 'VM_OPERATOR', 'VM_ADMINISTRATOR', 'NETWORK_ADMINISTRATOR', 'STORAGE_ADMINISTRATOR');")  # noqa
    op.execute("ALTER TABLE public.user_role ALTER COLUMN role TYPE role_types USING (role::text::role_types);")
    op.execute("UPDATE public.group_role  SET role = 'ADMINISTRATOR' WHERE role IN ('READ_ONLY', 'VM_OPERATOR', 'VM_ADMINISTRATOR', 'NETWORK_ADMINISTRATOR', 'STORAGE_ADMINISTRATOR');")  # noqa
    op.execute("ALTER TABLE public.group_role ALTER COLUMN role TYPE role_types USING (role::text::role_types);")
    op.execute("UPDATE public.entity_role_owner SET role = 'ADMINISTRATOR' WHERE role IN ('READ_ONLY', 'VM_OPERATOR', 'VM_ADMINISTRATOR', 'NETWORK_ADMINISTRATOR', 'STORAGE_ADMINISTRATOR');")  # noqa
    op.execute("ALTER TABLE public.entity_role_owner ALTER COLUMN role TYPE role_types USING (role::text::role_types);")
    op.execute("DROP TYPE IF EXISTS role CASCADE;")


def downgrade():
    # TODO: обратная миграция?
    pass
