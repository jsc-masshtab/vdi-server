"""x2go connection type

Revision ID: 90d353c9e3f7
Revises: f8b9f6b669a9
Create Date: 2021-09-07 13:58:06.431702

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '90d353c9e3f7'
down_revision = 'f8b9f6b669a9'
branch_labels = None
depends_on = None


enum_name = 'poolconnectiontypes'
old_protocols = ["SPICE",
                 "SPICE_DIRECT",
                 "RDP",
                 "NATIVE_RDP"
                 ]
new_value = 'X2GO'
new_protocols = [*old_protocols, new_value]

old_type = sa.Enum(*old_protocols, name=enum_name)
new_type = sa.Enum(*new_protocols, name=enum_name)


def upgrade():
    op.execute("ALTER TYPE " + enum_name + " RENAME TO old_type;")

    # Create new enum type
    new_type.create(op.get_bind())

    # Update column to use new enum type
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types TYPE " + "poolconnectiontypes[]" +
               " USING connection_types::text::" + "poolconnectiontypes[]")

    op.execute("ALTER TABLE active_tk_connection ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    # Drop old enum type
    op.execute("DROP TYPE old_type")


def downgrade():
    # Remove x2go from array
    op.execute("UPDATE pool SET connection_types = array_remove(connection_types, 'X2GO'::poolconnectiontypes);")
    op.execute("UPDATE active_tk_connection SET connection_type = null WHERE connection_type = 'X2GO'::poolconnectiontypes;")
    op.execute("ALTER TYPE " + enum_name + " RENAME TO new_type;")

    # Create old  enum type
    old_type.create(op.get_bind())

    # Update column to use old enum type
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types TYPE " + "poolconnectiontypes[]" +
               " USING connection_types::text::" + "poolconnectiontypes[]")

    op.execute("ALTER TABLE active_tk_connection ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    # Drop new enum type
    op.execute("DROP TYPE new_type")
