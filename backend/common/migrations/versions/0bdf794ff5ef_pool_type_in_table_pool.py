"""pool_type_in_table_pool

Revision ID: 0bdf794ff5ef
Revises: 3afef08f92e4
Create Date: 2021-06-16 14:16:20.538406

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0bdf794ff5ef'
down_revision = '3afef08f92e4'
branch_labels = None
depends_on = None

enum_name = 'pooltypes'
enum_type = sa.Enum('AUTOMATED', 'STATIC', 'GUEST', 'RDS', name=enum_name)


def upgrade():

    enum_type.create(op.get_bind())

    # Add column
    op.add_column('pool', sa.Column('pool_type', enum_type, nullable=True))

    # Fill existing rows
    op.execute("""
                 UPDATE pool
                     SET pool_type = CASE
                         WHEN automated_pool.is_guest = TRUE THEN 'GUEST'::pooltypes
                         WHEN automated_pool.is_guest = FALSE THEN 'AUTOMATED'::pooltypes
                         END
                 FROM automated_pool
                 WHERE automated_pool.id = pool.id
             """)

    op.execute("""
                 UPDATE pool
                     SET pool_type = 'STATIC'::pooltypes
                 FROM static_pool
                 WHERE static_pool.id = pool.id
             """)

    op.execute("""
                 UPDATE pool
                     SET pool_type = 'RDS'::pooltypes
                 FROM rds_pool
                 WHERE rds_pool.id = pool.id
             """)

    # Make non-null
    op.alter_column(table_name='pool', column_name='pool_type', nullable=False)


def downgrade():
    op.execute('DROP TYPE ' + enum_name + ' CASCADE')
