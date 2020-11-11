"""add_task_type_vm_prepare

Revision ID: a3ec8742ed81
Revises: 024c1baa4591
Create Date: 2020-11-11 10:47:03.116541

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a3ec8742ed81'
down_revision = '024c1baa4591'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TYPE task_type CASCADE;")

    task_type = postgresql.ENUM('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL', 'DECREASING_POOL', 'VM_PREPARE',
                                name='task_type')
    task_type.create(op.get_bind())
    # Только в этой версии таблица перестает очищаться, поэтому очищаем ее в последний раз для применения миграции
    op.execute('truncate table task;')
    op.add_column('task', sa.Column('task_type', sa.Enum('CREATING_POOL', 'EXPANDING_POOL',
                                                         'DELETING_POOL', 'DECREASING_POOL', 'VM_PREPARE',
                                                         name='task_type'), nullable=False))

    op.create_index(op.f('ix_task_task_type'), 'task', ['task_type'], unique=False)


def downgrade():
    op.execute("DROP TYPE task_type CASCADE;")

    task_type = postgresql.ENUM('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL', 'DECREASING_POOL', name='task_type')
    task_type.create(op.get_bind())

    op.add_column('task', sa.Column('task_type', sa.Enum('CREATING_POOL', 'EXPANDING_POOL',
                                                         'DELETING_POOL', 'DECREASING_POOL',
                                                         name='task_type'), nullable=False))

    op.create_index(op.f('ix_task_task_type'), 'task', ['task_type'], unique=False)
