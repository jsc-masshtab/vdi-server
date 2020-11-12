"""change_task_types_names

Revision ID: 063f3ac2641c
Revises: a3ec8742ed81
Create Date: 2020-11-12 15:39:01.073810

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '063f3ac2641c'
down_revision = 'a3ec8742ed81'
branch_labels = None
depends_on = None


def upgrade():
    # create temp enum
    task_type_temp = postgresql.ENUM('POOL_CREATE', 'POOL_EXPAND', 'POOL_DELETE',
                                     'POOL_DECREASE', 'VM_PREPARE', name='task_type_temp')
    task_type_temp.create(op.get_bind())

    new_enum = sa.Enum('POOL_CREATE', 'POOL_EXPAND', 'POOL_DELETE',
                            'POOL_DECREASE', 'VM_PREPARE', name='task_type_temp')
    op.add_column('task', sa.Column('task_type_temp', new_enum, nullable=True))

    # Copy data from task_type column
    op.execute("""UPDATE task
                  SET task_type_temp = CASE task.task_type 
                                       WHEN 'CREATING_POOL' THEN 'POOL_CREATE' 
                                       WHEN 'EXPANDING_POOL' THEN 'POOL_EXPAND'
                                       WHEN 'DELETING_POOL' THEN 'POOL_DELETE'
                                       WHEN 'DECREASING_POOL' THEN 'POOL_DECREASE'
                                       WHEN 'VM_PREPARE' THEN 'VM_PREPARE'
                                       ELSE task_type_temp
                                       END
               """)

    # delete old type
    op.execute("DROP TYPE task_type CASCADE;")

    # rename type and column (task_type_temp -> task_type)
    op.execute("ALTER TYPE task_type_temp RENAME TO task_type;")
    op.execute("ALTER TABLE task RENAME COLUMN task_type_temp TO task_type;")

    # make column task_type_temp non-nullable
    op.alter_column('task', 'task_type', existing_type=new_enum, nullable=False)


def downgrade():
    pass
