"""astra admin user

Revision ID: db24ab713002
Revises: ef39174d595c
Create Date: 2021-02-04 12:08:23.206597

"""
from alembic import op
from common.veil.auth.hashers import make_password
from common.settings import SECRET_KEY

# revision identifiers, used by Alembic.
revision = 'db24ab713002'
down_revision = '80d82b9cbd8a'
branch_labels = None
depends_on = None


def upgrade():
    # Уникальный хэш для установки
    hashed_password = make_password(password='Bazalt1!', salt=SECRET_KEY)
    # Создаем пользователя аналогично пользователю из установки
    sql = """insert
                 into
                 public."user" (id, username, password, is_active, is_superuser)
                 values (
                    'f9599771-cc95-45e5-9ae5-c8177b796aff',
                    'vdiadmin',
                    '{}',
                    true,
                    true);""".format(hashed_password)
    op.execute(sql)


def downgrade():
    op.execute("delete from public.user where id = 'f9599771-cc95-45e5-9ae5-c8177b796aff';")
