"""Create_table_user_tk_permission

Revision ID: 2b3a6970de80
Revises: 01569a298c33
Create Date: 2020-12-17 12:05:38.409738

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '2b3a6970de80'
down_revision = '01569a298c33'
branch_labels = None
depends_on = None


def upgrade():

    permissions_enum = sa.Enum('USB_REDIR', 'FOLDERS_REDIR', name='tk_permission')

    # user_tk_permission
    user_tk_permission_table = op.create_table('user_tk_permission',
                                               sa.Column('id', postgresql.UUID(), nullable=False),
                                               sa.Column('permission',
                                                         permissions_enum,
                                                         nullable=False),
                                               sa.Column('user_id', postgresql.UUID(), nullable=True),
                                               sa.PrimaryKeyConstraint('id'),
                                               sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
                                               )
    op.create_index(op.f('ix_user_tk_permission'), 'user_tk_permission', ['permission'], unique=False)
    op.create_unique_constraint('permission_user_id_unique_constraint', 'user_tk_permission',
                                ['permission', 'user_id'])

    # group_tk_permission
    op.create_table('group_tk_permission',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('permission',
                              permissions_enum,
                              nullable=False),
                    sa.Column('group_id', postgresql.UUID(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
                    )
    op.create_index(op.f('ix_group_tk_permission'), 'group_tk_permission', ['permission'], unique=False)
    op.create_unique_constraint('permission_group_id_unique_constraint', 'group_tk_permission',
                                ['permission', 'group_id'])

    # Дать всем существующим пользователям все возможные права
    conn = op.get_bind()
    res = conn.execute("SELECT * FROM public.user")
    al_users = res.fetchall()

    user_tk_permissions = [
        {'id': str(uuid.uuid4()), 'permission': 'USB_REDIR', 'user_id': str(user[0])} for user in al_users]
    user_tk_permissions.extend([
        {'id': str(uuid.uuid4()), 'permission': 'FOLDERS_REDIR', 'user_id': str(user[0])} for user in al_users])

    # print('user_tk_permissions', user_tk_permissions)
    op.bulk_insert(user_tk_permission_table, user_tk_permissions)


def downgrade():

    # user_tk_permission
    op.drop_index(op.f('ix_user_tk_permission'), table_name='user_tk_permission')
    op.drop_table('user_tk_permission')

    # group_tk_permission
    op.drop_index(op.f('ix_group_tk_permission'), table_name='group_tk_permission')
    op.drop_table('group_tk_permission')

    op.execute("DROP TYPE tk_permission CASCADE")
