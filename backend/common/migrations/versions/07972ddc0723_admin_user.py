"""Admin_user.

Revision ID: 07972ddc0723
Revises: b58c521ba8d3
Create Date: 2022-01-19 12:21:44.174731

"""
from alembic import op

from common.settings import SECRET_KEY
from common.veil.auth.hashers import make_password

# revision identifiers, used by Alembic.
revision = "07972ddc0723"
down_revision = "b58c521ba8d3"
branch_labels = None
depends_on = None


def upgrade():
    # Уникальный хэш для установки
    hashed_password = make_password(password="Bazalt1!", salt=SECRET_KEY)
    # Создаем пользователя аналогично пользователю из установки
    sql = """insert
                 into
                 public."user" (id, username, password, local_password, by_ad, is_active, is_superuser, two_factor)
                 values (
                    'f9599771-cc95-45e5-9ae5-c8177b796aff',
                    'vdiadmin',
                    '{}',
                    true,
                    false,
                    true,
                    true,
                    false);""".format(
        hashed_password
    )
    op.execute(sql)


def downgrade():
    op.execute(
        "delete from public.user where id = 'f9599771-cc95-45e5-9ae5-c8177b796aff';"
    )
