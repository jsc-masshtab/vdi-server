"""added_loadplay_connection_type

Revision ID: 9f39f90cc36d
Revises: 39d6405e9691
Create Date: 2022-05-10 11:49:17.643149

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f39f90cc36d'
down_revision = '39d6405e9691'
branch_labels = None
depends_on = None


enum_name = "poolconnectiontypes"
old_protocols = ["SPICE",
                 "SPICE_DIRECT",
                 "RDP",
                 "NATIVE_RDP",
                 "X2GO"
                 ]
new_value = "LOADPLAY"
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

    op.execute("ALTER TABLE tk_vm_connection ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    op.execute("ALTER TABLE vm_connection_data ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    # Drop old enum type
    op.execute("DROP TYPE old_type")


def downgrade():
    # Remove LOADPLAY
    op.execute("UPDATE pool SET connection_types = array_remove(connection_types, 'LOADPLAY'::poolconnectiontypes);")
    op.execute(
        "UPDATE tk_vm_connection SET connection_type = null WHERE connection_type = 'LOADPLAY'::poolconnectiontypes;")
    op.execute("DELETE FROM vm_connection_data WHERE connection_type = 'LOADPLAY'::poolconnectiontypes;")

    op.execute("ALTER TYPE " + enum_name + " RENAME TO new_type;")

    # Create old  enum type
    old_type.create(op.get_bind())

    # Update column to use old enum type
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types TYPE " + "poolconnectiontypes[]" +
               " USING connection_types::text::" + "poolconnectiontypes[]")

    op.execute("ALTER TABLE tk_vm_connection ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    op.execute("ALTER TABLE vm_connection_data ALTER COLUMN connection_type TYPE " + "poolconnectiontypes" +
               " USING connection_type::text::" + "poolconnectiontypes")

    # Drop new enum type
    op.execute("DROP TYPE new_type")
