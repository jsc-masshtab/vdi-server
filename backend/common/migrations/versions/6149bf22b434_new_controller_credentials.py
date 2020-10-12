"""new controller credentials

Revision ID: 6149bf22b434
Revises: 3bdd27d82159
Create Date: 2020-07-06 14:03:43.149961

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6149bf22b434'
down_revision = '836f611f1cab'
branch_labels = None
depends_on = None


def upgrade():
    # Деактивация существующих записей контроллера и пулов
    op.execute("""update public.controller set status='FAILED' where controller.status = 'ACTIVE'""")
    op.execute("""update public.pool set status ='FAILED' where status = 'ACTIVE'""")
    # Модификация таблицы контроллера
    op.create_unique_constraint(None, 'automated_pool', ['id'])
    op.alter_column('controller', 'token',
                    existing_type=sa.VARCHAR(length=1024),
                    nullable=False)
    op.drop_column('controller', 'expires_on')
    op.drop_column('controller', 'ldap_connection')
    op.drop_column('controller', 'password')
    op.drop_column('controller', 'username')
    op.create_unique_constraint(None, 'pool', ['id'])
    op.create_unique_constraint(None, 'static_pool', ['id'])
    op.create_index(op.f('ix_controller_address'), 'controller', ['address'], unique=True)
    op.drop_constraint('controller_address_key', 'controller', type_='unique')


def downgrade():
    # Обратная миграция маловероятна, т.к. будет исключен код отвечающий за авторизацию.
    op.create_unique_constraint('controller_address_key', 'controller', ['address'])
    op.drop_index(op.f('ix_controller_address'), table_name='controller')
    # Деактивация существующих записей контроллера и пулов
    op.execute("""update public.controller set status='FAILED' where controller.status = 'ACTIVE'""")
    op.execute("""update public.pool set status ='FAILED' where status = 'ACTIVE'""")
    # Модификация таблицы контроллера
    op.add_column('controller', sa.Column('username', sa.VARCHAR(length=128), autoincrement=False, nullable=False))
    op.add_column('controller', sa.Column('password', sa.VARCHAR(length=128), autoincrement=False, nullable=False))
    op.add_column('controller', sa.Column('ldap_connection', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('controller',
                  sa.Column('expires_on', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.alter_column('controller', 'token',
                    existing_type=sa.VARCHAR(length=1024),
                    nullable=True)
    op.drop_constraint('automated_pool_id_key', 'automated_pool', type_='unique')
    op.drop_constraint('pool_id_key', 'pool', type_='unique')
    op.drop_constraint('static_pool_id_key', 'static_pool', type_='unique')
