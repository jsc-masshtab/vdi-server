"""Task feild created

Revision ID: 2e402a48baca
Revises: 7160da1c3c23
Create Date: 2020-10-05 11:44:51.631412

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2e402a48baca'
down_revision = '7160da1c3c23'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task', sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                                    nullable=True))

    op.drop_column('task', 'task_type')

    task_type = postgresql.ENUM('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL', name='task_type')
    task_type.create(op.get_bind())
    op.add_column('task', sa.Column('task_type', sa.Enum('CREATING_POOL', 'EXPANDING_POOL', 'DELETING_POOL',
                                                         name='task_type'), nullable=False))


def downgrade():
    op.drop_column('task', 'created')

    op.execute("DROP TYPE task_type CASCADE;")

    op.add_column('task', sa.Column('task_type', sa.VARCHAR(length=128), autoincrement=False, nullable=False))
