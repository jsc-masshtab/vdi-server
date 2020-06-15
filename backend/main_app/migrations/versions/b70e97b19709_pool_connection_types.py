"""Pool connection types

Revision ID: b70e97b19709
Revises: 96d866b36fa2
Create Date: 2020-04-19 21:27:58.406268

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b70e97b19709'
down_revision = '96d866b36fa2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE pool_connection_types AS ENUM ('SPICE', 'RDP', 'NATIVE_RDP');")
    op.execute("ALTER TABLE pool ADD COLUMN IF NOT EXISTS connection_types pool_connection_types ARRAY;")
    op.execute("UPDATE pool SET connection_types = '{SPICE}' WHERE connection_types IS NULL;")
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types SET NOT NULL;")
    op.create_index(op.f('ix_pool_connection_types'), 'pool', ['connection_types'], unique=False)


def downgrade():
    op.execute("ALTER TABLE pool DROP COLUMN connection_types;")
    op.execute("DROP TYPE pool_connection_types;")
    op.drop_index(op.f('ix_pool_connection_types'), table_name='pool')
