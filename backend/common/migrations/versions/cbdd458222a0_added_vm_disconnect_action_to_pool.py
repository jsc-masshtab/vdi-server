"""added vm disconnect action to pool

Revision ID: cbdd458222a0
Revises: ba1b6817b510
Create Date: 2021-10-12 15:17:39.213404

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cbdd458222a0'
down_revision = 'ba1b6817b510'
branch_labels = None
depends_on = None


enum_name = 'vmactionuponuserdisconnect'
enum_list = ['NONE',
             'RECREATE',
             'SHUTDOWN',
             'SHUTDOWN_FORCED',
             'SUSPEND']
enum_type = postgresql.ENUM(*enum_list, name=enum_name)


def upgrade():
    enum_type.create(op.get_bind())

    op.add_column('pool', sa.Column('vm_action_upon_user_disconnect',
                                    sa.Enum(*enum_list, name=enum_name),
                                    server_default="NONE",
                                    nullable=False))

    op.add_column('pool', sa.Column('vm_disconnect_action_timeout',
                                    sa.Integer(),
                                    server_default="60",
                                    nullable=False))

    op.drop_column('automated_pool', 'waiting_time')


def downgrade():

    op.add_column('automated_pool', sa.Column('waiting_time',
                                              sa.Integer(),
                                              nullable=True))

    op.drop_column('pool', 'vm_disconnect_action_timeout')

    op.drop_column('pool', 'vm_action_upon_user_disconnect')

    op.execute("DROP TYPE " + enum_name)
