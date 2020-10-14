"""add SPICE_DIRECT to PoolConnectionTypes

Revision ID: 8851d2ea916b
Revises: 0f99d16903fd
Create Date: 2020-10-13 14:29:46.529534

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '8851d2ea916b'
down_revision = '0f99d16903fd'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TYPE pool_connection_types CASCADE;")

    op.execute("CREATE TYPE pool_connection_types AS ENUM ('SPICE', 'SPICE_DIRECT', 'RDP', 'NATIVE_RDP');")
    op.execute("ALTER TABLE pool ADD COLUMN IF NOT EXISTS connection_types pool_connection_types ARRAY;")
    op.execute("UPDATE pool SET connection_types = '{SPICE}' WHERE connection_types IS NULL;")
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types SET NOT NULL;")
    op.create_index(op.f('ix_pool_connection_types'), 'pool', ['connection_types'], unique=False)


def downgrade():
    op.execute("DROP TYPE pool_connection_types CASCADE;")

    op.execute("CREATE TYPE pool_connection_types AS ENUM ('SPICE', 'RDP', 'NATIVE_RDP');")
    op.execute("ALTER TABLE pool ADD COLUMN IF NOT EXISTS connection_types pool_connection_types ARRAY;")
    op.execute("UPDATE pool SET connection_types = '{SPICE}' WHERE connection_types IS NULL;")
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types SET NOT NULL;")
    op.create_index(op.f('ix_pool_connection_types'), 'pool', ['connection_types'], unique=False)
