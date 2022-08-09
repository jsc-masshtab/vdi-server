"""Remove x2Go

Revision ID: 4877bb8b4f29
Revises: b755ef9b17a2
Create Date: 2022-08-09 15:36:12.037672

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4877bb8b4f29'
down_revision = 'b755ef9b17a2'
branch_labels = None
depends_on = None


enum_name = "poolconnectiontypes"
new_protocols = ["SPICE",
                 "SPICE_DIRECT",
                 "RDP",
                 "NATIVE_RDP",
                 "LOADPLAY"
                 ]
value_to_remove = "X2GO"
old_protocols = [*new_protocols, value_to_remove]

old_type = sa.Enum(*old_protocols, name=enum_name)
new_type = sa.Enum(*new_protocols, name=enum_name)


def upgrade():
    # Remove X2GO
    op.execute("UPDATE pool SET connection_types = array_remove(connection_types, 'X2GO'::poolconnectiontypes);")
    op.execute(
        "UPDATE tk_vm_connection SET connection_type = null WHERE connection_type = 'X2GO'::poolconnectiontypes;")
    op.execute("DELETE FROM vm_connection_data WHERE connection_type = 'X2GO'::poolconnectiontypes;")

    op.execute("ALTER TYPE " + enum_name + " RENAME TO old_type;")

    # Create new enum type
    new_type.create(op.get_bind())

    # Update column to use new enum type
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types TYPE poolconnectiontypes[] "
               "USING connection_types::text::poolconnectiontypes[]")

    op.execute("ALTER TABLE tk_vm_connection ALTER COLUMN connection_type TYPE poolconnectiontypes "
               "USING connection_type::text::poolconnectiontypes")

    op.execute("ALTER TABLE vm_connection_data ALTER COLUMN connection_type TYPE poolconnectiontypes "
               "USING connection_type::text::poolconnectiontypes")

    # Drop old enum type
    op.execute("DROP TYPE old_type")


def downgrade():
    op.execute("ALTER TYPE " + enum_name + " RENAME TO new_type;")

    # Create old enum type
    old_type.create(op.get_bind())

    # Update column to use old enum type
    op.execute("ALTER TABLE pool ALTER COLUMN connection_types TYPE poolconnectiontypes[] "
               "USING connection_types::text::poolconnectiontypes[]")

    op.execute("ALTER TABLE tk_vm_connection ALTER COLUMN connection_type TYPE poolconnectiontypes "
               "USING connection_type::text::poolconnectiontypes")

    op.execute("ALTER TABLE vm_connection_data ALTER COLUMN connection_type TYPE poolconnectiontypes "
               "USING connection_type::text::poolconnectiontypes")

    # Drop old enum type
    op.execute("DROP TYPE new_type")