"""add_tk_permission_shared_clipboard

Revision ID: 52224f9ec674
Revises: 2b3a6970de80
Create Date: 2021-01-21 10:10:16.201887

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from common.models.user_tk_permission import UserTkPermission

# revision identifiers, used by Alembic.
revision = '52224f9ec674'
down_revision = '2b3a6970de80'
branch_labels = None
depends_on = None


old_permissions_list = ['USB_REDIR', 'FOLDERS_REDIR']
new_permissions_list = ['USB_REDIR', 'FOLDERS_REDIR', 'SHARED_CLIPBOARD']
old_permissions_type_name = 'tk_permission'
new_permissions_type_name = 'tkpermission'


def grant_all_permissions(permissions_list):
    # Дать всем существующим пользователям все возможные права
    conn = op.get_bind()
    res = conn.execute("SELECT * FROM public.user")
    al_users = res.fetchall()

    user_tk_permissions = []
    for user in al_users:
        for permission in permissions_list:
            user_tk_permissions.append(
                {'id': str(uuid.uuid4()), 'permission': permission, 'user_id': str(user[0])})

    # user_tk_permission_table = table('user_tk_permission')
    op.bulk_insert(UserTkPermission.__table__, user_tk_permissions)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.execute("DROP TYPE {} CASCADE;".format(old_permissions_type_name))
    new_permissions_enum = postgresql.ENUM(*new_permissions_list, name=new_permissions_type_name)
    new_permissions_enum.create(op.get_bind())

    # group
    op.execute('truncate table group_tk_permission;')

    op.alter_column('group_tk_permission', 'group_id', existing_type=postgresql.UUID(), nullable=False)

    op.add_column('group_tk_permission',
                  sa.Column('permission',
                            sa.Enum(*new_permissions_list, name=new_permissions_type_name),
                            nullable=False))

    op.create_index(op.f('ix_group_tk_permission'), 'group_tk_permission', ['permission'], unique=False)
    op.create_unique_constraint('permission_group_id_unique_constraint', 'group_tk_permission',
                                ['permission', 'group_id'])

    # user
    op.execute('truncate table user_tk_permission;')

    op.alter_column('user_tk_permission', 'user_id', existing_type=postgresql.UUID(), nullable=False)

    op.add_column('user_tk_permission',
                  sa.Column('permission',
                            sa.Enum(*new_permissions_list, name=new_permissions_type_name),
                            nullable=False))

    op.create_index(op.f('ix_user_tk_permission'), 'user_tk_permission', ['permission'], unique=False)
    op.create_unique_constraint('permission_user_id_unique_constraint', 'user_tk_permission',
                                ['permission', 'user_id'])

    # Дать всем существующим пользователям все возможные права
    grant_all_permissions(new_permissions_list)


def downgrade():

    op.execute("DROP TYPE {} CASCADE;".format(new_permissions_type_name))
    old_permissions_enum = postgresql.ENUM(*old_permissions_list, name=old_permissions_type_name)
    old_permissions_enum.create(op.get_bind())

    # group
    op.execute('truncate table group_tk_permission;')

    op.alter_column('group_tk_permission', 'group_id', existing_type=postgresql.UUID(), nullable=True)

    op.add_column('group_tk_permission', sa.Column('permission',
                  sa.Enum(*old_permissions_list, name=old_permissions_type_name),
                  nullable=False))

    op.create_index(op.f('ix_group_tk_permission'), 'group_tk_permission', ['permission'], unique=False)

    # user
    op.execute('truncate table user_tk_permission;')

    op.alter_column('user_tk_permission', 'user_id', existing_type=postgresql.UUID(), nullable=True)

    op.add_column('user_tk_permission', sa.Column('permission',
                  sa.Enum(*old_permissions_list, name=old_permissions_type_name),
                  nullable=False))

    op.create_index(op.f('ix_user_tk_permission'), 'user_tk_permission', ['permission'], unique=False)

    # Дать всем существующим пользователям все возможные права
    grant_all_permissions(old_permissions_list)