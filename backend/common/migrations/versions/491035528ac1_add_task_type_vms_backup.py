"""Add_task_type_vms_backup

Revision ID: 491035528ac1
Revises: 25b755d488b3
Create Date: 2021-02-17 13:20:06.259586

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '491035528ac1'
down_revision = '25b755d488b3'
branch_labels = None
depends_on = None


enum_name = 'task_type'

old_options = ['POOL_CREATE', 'POOL_EXPAND', 'POOL_DELETE', 'POOL_DECREASE', 'VM_PREPARE']
new_options = [*old_options, 'VMS_BACKUP']

old_type = sa.Enum(*old_options, name='task_type')
new_type = sa.Enum(*new_options, name='task_type')


def upgrade():
    # Rename current enum type to _old
    op.execute("ALTER TYPE task_type RENAME TO task_type_old;")

    # Create new enum type
    new_type.create(op.get_bind())

    # Update column to use new enum type
    op.execute('ALTER TABLE task ALTER COLUMN task_type TYPE ' + enum_name + ' USING task_type::text::' + enum_name)

    # Drop old enum type
    op.execute('DROP TYPE task_type_old')


def downgrade():
    # Delete tasks with type VMS_BACKUP
    op.execute("DELETE FROM public.task WHERE task_type = 'VMS_BACKUP';")

    # Rename current enum type to _new
    op.execute("ALTER TYPE task_type RENAME TO task_type_new;")

    # Create old enum type
    old_type.create(op.get_bind())

    # Update column to use old enum type
    op.execute('ALTER TABLE task ALTER COLUMN task_type TYPE ' + enum_name + ' USING task_type::text::' + enum_name)

    # Drop new enum type
    op.execute('DROP TYPE task_type_new')
