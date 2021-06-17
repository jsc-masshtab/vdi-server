"""split_clipboard_permissions

Revision ID: f650be39c164
Revises: 70220709e7b8
Create Date: 2021-06-10 11:40:01.148136

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f650be39c164'
down_revision = '70220709e7b8'
branch_labels = None
depends_on = None


enum_name = 'tkpermission'
temp_enum_name = 'tkpermission_new'
old_options = ['USB_REDIR', 'FOLDERS_REDIR', 'SHARED_CLIPBOARD']
new_options = ['USB_REDIR', 'FOLDERS_REDIR', 'SHARED_CLIPBOARD_CLIENT_TO_GUEST', 'SHARED_CLIPBOARD_GUEST_TO_CLIENT']

old_type = sa.Enum(*old_options, name=enum_name)
new_type = sa.Enum(*new_options, name=temp_enum_name)


def upgrade():
    """По факту производится разбитие SHARED_CLIPBOARD на SHARED_CLIPBOARD_CLIENT_TO_GUEST
     и SHARED_CLIPBOARD_GUEST_TO_CLIENT"""

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create new enum type
    new_type.create(op.get_bind())

    # Groups

    # Add column "permission_new" with updated type
    op.add_column("group_tk_permission", sa.Column("permission_new", new_type, nullable=True))  # later make nullable=False

    # Fill column "permission_new" based on data in column "permission"
    # SHARED_CLIPBOARD по факту будет заменено на SHARED_CLIPBOARD_CLIENT_TO_GUEST и SHARED_CLIPBOARD_GUEST_TO_CLIENT
    # Сначала сделаем апдейты.
    op.execute("""UPDATE group_tk_permission
                    SET permission_new = CASE permission
                        WHEN 'USB_REDIR' THEN 'USB_REDIR'::tkpermission_new
                        WHEN 'FOLDERS_REDIR' THEN 'FOLDERS_REDIR'::tkpermission_new
                        WHEN 'SHARED_CLIPBOARD' THEN 'SHARED_CLIPBOARD_CLIENT_TO_GUEST'::tkpermission_new
                END
    """)

    # Drop old column "permission"
    op.drop_column("group_tk_permission", "permission")

    # Затем добавим новые записи (c SHARED_CLIPBOARD_GUEST_TO_CLIENT)
    op.execute("""
        INSERT INTO group_tk_permission (id, group_id, permission_new)
            SELECT uuid_generate_v4(), t.group_id, 'SHARED_CLIPBOARD_GUEST_TO_CLIENT'::tkpermission_new
            FROM group_tk_permission t
        WHERE t.permission_new = 'SHARED_CLIPBOARD_CLIENT_TO_GUEST'
    """)

    # Rename "permission_new" to "permission" and make it non-null
    op.alter_column(table_name='group_tk_permission',
                    column_name='permission_new',
                    new_column_name='permission',
                    nullable=False)

    # Restore unique_constraint
    op.create_unique_constraint("permission_group_id_unique_constraint",
                                "group_tk_permission",
                                ["permission", "group_id"])
    # Restore index
    op.create_index(
        op.f("ix_group_tk_permission_permission"),
        "group_tk_permission",
        ["permission"],
        unique=False,
    )

    # Users

    # Add column "permission_new" with updated type
    op.add_column("user_tk_permission", sa.Column("permission_new", new_type, nullable=True))  # later make nullable=False

    # Fill column "permission_new" based on data in column "permission"
    # SHARED_CLIPBOARD по факту будет заменено на SHARED_CLIPBOARD_CLIENT_TO_GUEST и SHARED_CLIPBOARD_GUEST_TO_CLIENT
    # Сначала сделаем апдейты.
    op.execute("""UPDATE user_tk_permission
                    SET permission_new = CASE permission
                        WHEN 'USB_REDIR' THEN 'USB_REDIR'::tkpermission_new
                        WHEN 'FOLDERS_REDIR' THEN 'FOLDERS_REDIR'::tkpermission_new
                        WHEN 'SHARED_CLIPBOARD' THEN 'SHARED_CLIPBOARD_CLIENT_TO_GUEST'::tkpermission_new
                END
    """)

    # Drop old column "permission"
    op.drop_column("user_tk_permission", "permission")

    # Затем добавим новые записи (c SHARED_CLIPBOARD_GUEST_TO_CLIENT)
    op.execute("""
        INSERT INTO user_tk_permission (id, user_id, permission_new)
            SELECT uuid_generate_v4(), t.user_id, 'SHARED_CLIPBOARD_GUEST_TO_CLIENT'::tkpermission_new
            FROM user_tk_permission t
        WHERE t.permission_new = 'SHARED_CLIPBOARD_CLIENT_TO_GUEST'
    """)

    # Rename "permission_new" to "permission" and make it NOT null
    op.alter_column(table_name='user_tk_permission',
                    column_name='permission_new',
                    new_column_name='permission',
                    nullable=False)

    # Restore unique_constraint
    op.create_unique_constraint("permission_user_id_unique_constraint",
                                "user_tk_permission",
                                ["permission", "user_id"])

    # Restore index
    op.create_index(
        op.f("ix_user_tk_permission_permission"),
        "user_tk_permission",
        ["permission"],
        unique=False,
    )

    # Restore type name
    old_type.drop(op.get_bind(), checkfirst=False)
    op.execute('ALTER TYPE ' + temp_enum_name + ' RENAME TO ' + enum_name)


def downgrade():
    """Возвращаем старый тип, даем все разрешения существующим пользователям"""

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.execute("TRUNCATE TABLE group_tk_permission;")
    op.execute("TRUNCATE TABLE user_tk_permission;")

    op.execute('DROP TYPE ' + enum_name + ' CASCADE')

    # Create old enum type
    old_type.create(op.get_bind())

    #  Add columns
    op.add_column("group_tk_permission", sa.Column("permission", old_type, nullable=False))
    op.add_column("user_tk_permission", sa.Column("permission", old_type, nullable=False))

    # Restore unique_constraint
    op.create_unique_constraint("permission_group_id_unique_constraint",
                                "group_tk_permission",
                                ["permission", "group_id"])
    op.create_unique_constraint("permission_user_id_unique_constraint",
                                "user_tk_permission",
                                ["permission", "user_id"])

    # Restore index
    op.create_index(
        op.f("ix_group_tk_permission_permission"),
        "group_tk_permission",
        ["permission"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_tk_permission_permission"),
        "user_tk_permission",
        ["permission"],
        unique=False,
    )

    # Give all permissions to users
    for permission_type in old_options:
        op.execute("""
           INSERT INTO user_tk_permission (id, user_id, permission)
                SELECT uuid_generate_v4(), u.id, '%s'::tkpermission
                FROM public.user u
        """ % permission_type)
