"""task_add_task_type_decreasing_pool

Revision ID: 69d6bd97f61e
Revises: b7aab201716b
Create Date: 2020-10-20 10:46:08.924765

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '69d6bd97f61e'
down_revision = 'b7aab201716b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TYPE task_type CASCADE;")

    task_type = postgresql.ENUM('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL', 'DECREASING_POOL', name='task_type')
    task_type.create(op.get_bind())

    op.add_column('task', sa.Column('task_type', sa.Enum('CREATING_POOL', 'EXPANDING_POOL',
                                                         'DELETING_POOL', 'DECREASING_POOL',
                                                         name='task_type'), nullable=False))

    op.create_index(op.f('ix_task_task_type'), 'task', ['task_type'], unique=False)


def downgrade():
    op.execute("DROP TYPE task_type CASCADE;")

    task_type = postgresql.ENUM('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL', name='task_type')
    task_type.create(op.get_bind())

    op.add_column('task', sa.Column('task_type', sa.Enum('CREATING_POOL', 'EXPANDING_POOL',
                                                         'DELETING_POOL', name='task_type'), nullable=False))

    op.create_index(op.f('ix_task_task_type'), 'task', ['task_type'], unique=False)
