"""pool table change structure v1

Revision ID: cc4dfc473fb6
Revises: c61c8ef17e40
Create Date: 2019-11-14 11:53:55.589523

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cc4dfc473fb6'
down_revision = 'c61c8ef17e40'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('vm')
    op.drop_table('pools_users')
    op.drop_table('pool')
    op.create_unique_constraint(None, 'controller', ['address'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'controller', type_='unique')
    op.create_table('pool',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('verbose_name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('controller', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('desktop_pool_type', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('deleted', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('dynamic_traits', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('datapool_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('cluster_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('node_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('template_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('initial_size', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('reserve_size', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_size', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('vm_name_template', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['controller'], ['controller.id'], name='pool_controller_fkey'),
    sa.PrimaryKeyConstraint('id', name='pool_pkey'),
    sa.UniqueConstraint('verbose_name', name='pool_verbose_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('pools_users',
    sa.Column('pool_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['pool_id'], ['pool.id'], name='pools_users_pool_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='pools_users_user_id_fkey')
    )
    op.create_table('vm',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('template_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('pool_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('username', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['pool_id'], ['pool.id'], name='vm_pool_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='vm_pkey')
    )
    # ### end Alembic commands ###