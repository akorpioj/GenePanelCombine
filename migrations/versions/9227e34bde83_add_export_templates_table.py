"""Add export templates table

Revision ID: 9227e34bde83
Revises: 3d43d3ddbfa5
Create Date: 2025-10-13 10:19:04.948047

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9227e34bde83'
down_revision = '3d43d3ddbfa5'
branch_labels = None
depends_on = None


def upgrade():
    # Create export_templates table
    op.create_table(
        'export_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('include_metadata', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_versions', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_genes', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('filename_pattern', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_template_name')
    )
    
    # Create indexes
    op.create_index('idx_export_templates_user', 'export_templates', ['user_id'])
    op.create_index('idx_export_templates_default', 'export_templates', ['user_id', 'is_default'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_export_templates_default', table_name='export_templates')
    op.drop_index('idx_export_templates_user', table_name='export_templates')
    
    # Drop table
    op.drop_table('export_templates')
