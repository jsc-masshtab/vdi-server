"""Task type column to string

Revision ID: ba1b6817b510
Revises: 6d4gr26hpv7a
Create Date: 2021-10-07 15:29:40.480245

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ba1b6817b510'
down_revision = '6d4gr26hpv7a'
branch_labels = None
depends_on = None

enum_name = 'pooltasktype'
enum_type = postgresql.ENUM('POOL_CREATE', 'POOL_EXPAND', 'POOL_DELETE', 'POOL_DECREASE',
                            'VM_PREPARE', 'VMS_BACKUP', 'VMS_REMOVE', 'VM_GUEST_RECREATION', name=enum_name)


def upgrade():
    # Alter type to Unicode
    op.alter_column('task', 'task_type',
               existing_type=enum_type,
               type_=sa.Unicode(length=256),
               existing_nullable=False)

    # Drop old enum type
    op.execute("DROP TYPE " + enum_name)


def downgrade():
    # Create enum type
    enum_type.create(op.get_bind())
    #
    op.execute("ALTER TABLE task ALTER COLUMN task_type TYPE " + enum_name + " USING task_type::text::" + enum_name)
