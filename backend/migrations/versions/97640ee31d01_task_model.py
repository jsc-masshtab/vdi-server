"""task_model

Revision ID: 97640ee31d01
Revises: 3bdd27d82159
Create Date: 2020-07-13 17:01:53.070314

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '97640ee31d01'
down_revision = '3bdd27d82159'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('entity_id', postgresql.UUID(), nullable=True),
                    sa.Column('status',
                              sa.Enum('INITIAL', 'IN_PROGRESS', 'FAILED', 'CANCELLED', 'FINISHED', name='taskstatus'),
                              nullable=False),
                    sa.Column('task_type', sa.Unicode(length=128), nullable=False),
                    sa.Column('resume_on_app_startup', sa.Boolean(), nullable=False),
                    sa.Column('priority', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_task_status'), 'task', ['status'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_task_status'), table_name='task')
    op.drop_table('task')
    op.execute('DROP TYPE taskstatus CASCADE;')

    # ### end Alembic commands ###
