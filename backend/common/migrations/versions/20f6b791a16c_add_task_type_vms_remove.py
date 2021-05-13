"""Add task type VMs remove

Revision ID: 20f6b791a16c
Revises: 5f6ebf8486ec
Create Date: 2021-05-12 11:34:41.584371

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20f6b791a16c'
down_revision = '5f6ebf8486ec'
branch_labels = None
depends_on = None


enum_name = 'pooltasktype'
old_options = ['POOL_CREATE', 'POOL_EXPAND', 'POOL_DELETE', 'POOL_DECREASE', 'VM_PREPARE', 'VMS_BACKUP']
new_value = 'VMS_REMOVE'
new_options = [*old_options, new_value]

old_type = sa.Enum(*old_options, name=enum_name)
new_type = sa.Enum(*new_options, name=enum_name)


def upgrade():
    # Rename current enum type to old_type
    op.execute("ALTER TYPE " + enum_name + " RENAME TO old_type;")

    # Create new enum type
    new_type.create(op.get_bind())

    # Update column to use new enum type
    op.execute("ALTER TABLE task ALTER COLUMN task_type TYPE " + enum_name + " USING task_type::text::" + enum_name)

    # Drop old enum type
    op.execute("DROP TYPE old_type")


def downgrade():
    # Delete tasks with type  new_task_type
    op.execute("DELETE FROM public.task WHERE task_type = '{}'".format(new_value))

    # Rename current enum type to _new
    op.execute("ALTER TYPE " + enum_name + " RENAME TO new_type;")

    # Create old enum type
    old_type.create(op.get_bind())

    # Update column to use old enum type
    op.execute("ALTER TABLE task ALTER COLUMN task_type TYPE " + enum_name + " USING task_type::text::" + enum_name)

    # Drop new enum type
    op.execute("DROP TYPE new_type")
