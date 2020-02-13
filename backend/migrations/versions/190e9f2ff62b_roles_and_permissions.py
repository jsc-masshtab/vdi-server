"""Roles and Permissions

Revision ID: 190e9f2ff62b
Revises: 61a2865cbd10
Create Date: 2020-02-06 14:30:33.901427

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '190e9f2ff62b'
down_revision = '61a2865cbd10'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group_role',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('role', sa.Enum('READ_ONLY',
                                              'ADMINISTRATOR',
                                              'SECURITY_ADMINISTRATOR',
                                              'VM_ADMINISTRATOR',
                                              'NETWORK_ADMINISTRATOR',
                                              'STORAGE_ADMINISTRATOR',
                                              'VM_OPERATOR',
                                              name='role'), nullable=False),
                    sa.Column('group_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_group_role_role'), 'group_role', ['role'], unique=False)
    op.create_index('ix_group_roles_group_roles', 'group_role', ['role', 'group_id'], unique=True)
    op.create_table('role_entity_permission',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('permission', sa.Enum('VIEW', 'ADD', 'CHANGE', 'DELETE', name='permission'),
                              nullable=False),
                    sa.Column('role', sa.Enum('READ_ONLY',
                                              'ADMINISTRATOR',
                                              'SECURITY_ADMINISTRATOR',
                                              'VM_ADMINISTRATOR',
                                              'NETWORK_ADMINISTRATOR',
                                              'STORAGE_ADMINISTRATOR',
                                              'VM_OPERATOR',
                                              name='role'), nullable=False),
                    sa.Column('entity_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_role_entity_permission_permission'), 'role_entity_permission', ['permission'], unique=False)
    op.create_index(op.f('ix_role_entity_permission_role'), 'role_entity_permission', ['role'], unique=False)
    op.create_index('ix_role_entity_permission_role_entity_permission', 'role_entity_permission', ['permission', 'role', 'entity_id'], unique=True)
    op.create_table('user_role',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('role', sa.Enum('READ_ONLY',
                                              'ADMINISTRATOR',
                                              'SECURITY_ADMINISTRATOR',
                                              'VM_ADMINISTRATOR',
                                              'NETWORK_ADMINISTRATOR',
                                              'STORAGE_ADMINISTRATOR',
                                              'VM_OPERATOR',
                                              name='role'), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_role_role'), 'user_role', ['role'], unique=False)
    op.create_index('ix_user_roles_user_roles', 'user_role', ['role', 'user_id'], unique=True)
    op.create_index('ix_user_in_group', 'user_groups', ['user_id', 'group_id'], unique=True)
    op.drop_index('user_in_group', table_name='user_groups')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('user_in_group', 'user_groups', ['user_id', 'group_id'], unique=True)
    op.drop_index('ix_user_in_group', table_name='user_groups')
    op.drop_index('ix_user_roles_user_roles', table_name='user_role')
    op.drop_index(op.f('ix_user_role_role'), table_name='user_role')
    op.drop_table('user_role')
    op.drop_index('ix_role_entity_permission_role_entity_permission', table_name='role_entity_permission')
    op.drop_index(op.f('ix_role_entity_permission_role'), table_name='role_entity_permission')
    op.drop_index(op.f('ix_role_entity_permission_permission'), table_name='role_entity_permission')
    op.drop_table('role_entity_permission')
    op.drop_index('ix_group_roles_group_roles', table_name='group_role')
    op.drop_index(op.f('ix_group_role_role'), table_name='group_role')
    op.drop_table('group_role')
    # ### end Alembic commands ###
