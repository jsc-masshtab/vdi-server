"""roles reduction

Revision ID: a6f0e86cff98
Revises: 951435b7a90a
Create Date: 2020-12-21 16:03:53.581244

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a6f0e86cff98'
down_revision = '951435b7a90a'
branch_labels = None
depends_on = None


def upgrade():
    """Изменения таблицы владения сущностями.

    1. Переименовываем таблицу entity_role_owner
    2. Удаляем владение объектами с помощью ролей.
    3. Пересоздаем индексы
    """
    op.drop_index('ix_entity_role_owner_entity_role_group', table_name='entity_role_owner')
    op.drop_index('ix_entity_role_owner_entity_role_owner', table_name='entity_role_owner')
    op.drop_index('ix_entity_role_owner_entity_role_user', table_name='entity_role_owner')
    op.drop_index('ix_entity_role_owner_role', table_name='entity_role_owner')

    op.execute("""ALTER TABLE public.entity_role_owner DROP COLUMN role;""")
    op.execute("""ALTER TABLE public.entity_role_owner RENAME TO entity_owner;""")

    op.create_index('ix_entity_owner_entity_group', 'entity_owner', ['entity_id', 'group_id'], unique=True)
    op.create_index('ix_entity_owner_entity_owner', 'entity_owner', ['entity_id', 'group_id', 'user_id'], unique=True)
    op.create_index('ix_entity_owner_entity_user', 'entity_owner', ['entity_id', 'user_id'], unique=True)


def downgrade():
    """Возвращает все как было."""
    op.drop_index('ix_entity_owner_entity_group', table_name='entity_owner')
    op.drop_index('ix_entity_owner_entity_owner', table_name='entity_owner')
    op.drop_index('ix_entity_owner_entity_user', table_name='entity_owner')
    op.execute("""ALTER TABLE public.entity_owner RENAME TO entity_role_owner;""")
    op.execute("""ALTER TABLE public.entity_role_owner ADD COLUMN role role_types;""")
    op.create_index('ix_entity_role_owner_role', 'entity_role_owner', ['role'], unique=False)
    op.create_index('ix_entity_role_owner_entity_role_user', 'entity_role_owner', ['entity_id', 'role', 'user_id'], unique=True)
    op.create_index('ix_entity_role_owner_entity_role_owner', 'entity_role_owner', ['entity_id', 'role', 'group_id', 'user_id'], unique=True)
    op.create_index('ix_entity_role_owner_entity_role_group', 'entity_role_owner', ['entity_id', 'role', 'group_id'], unique=True)
