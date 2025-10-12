"""Add time format preference to users

Revision ID: 3d43d3ddbfa5
Revises: 951dc3f73d01
Create Date: 2025-10-12 19:01:09.780936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d43d3ddbfa5'
down_revision = '951dc3f73d01'
branch_labels = None
depends_on = None


def upgrade():
    # Add time_format_preference column to user table with default '24h'
    op.add_column('user', sa.Column('time_format_preference', sa.String(length=10), nullable=True))
    # Set default value for existing users
    op.execute("UPDATE \"user\" SET time_format_preference = '24h' WHERE time_format_preference IS NULL")


def downgrade():
    # Remove time_format_preference column from user table
    op.drop_column('user', 'time_format_preference')
