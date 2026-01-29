"""Add User, APIKey, Secret models for authentication and secrets management

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('FALSE'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )

    # Create api_keys table
    op.create_table('api_keys',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('api_key', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('FALSE'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('api_key')
    )

    # Create secrets table
    op.create_table('secrets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('key', sa.String(length=255), nullable=False),
    sa.Column('encrypted_value', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('FALSE'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'key', name='unique_user_secret_key')
    )

    # Add user_id column to tasks table
    op.add_column('tasks', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_tasks_user_id', 'tasks', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Remove user_id column from tasks table
    op.drop_constraint('fk_tasks_user_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'user_id')

    # Drop secrets table
    op.drop_table('secrets')

    # Drop api_keys table
    op.drop_table('api_keys')

    # Drop users table
    op.drop_table('users')