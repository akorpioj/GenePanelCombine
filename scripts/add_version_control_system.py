"""
Database migration to add version control enhancements

This migration adds support for:
- Version branches and tags
- Improved retention policy tracking
- Enhanced version metadata
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'add_version_control_system'
down_revision = '64ca2e43ca66'  # Previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types for version control
    op.execute("CREATE TYPE IF NOT EXISTS tagtype AS ENUM ('PRODUCTION', 'STAGING', 'RELEASE', 'HOTFIX', 'FEATURE', 'BACKUP')")
    op.execute("CREATE TYPE IF NOT EXISTS versiontype AS ENUM ('MAIN', 'BRANCH', 'TAG', 'MERGE')")
    
    # Create panel_version_tags table
    op.create_table('panel_version_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(length=100), nullable=False),
        sa.Column('tag_type', sa.Enum('PRODUCTION', 'STAGING', 'RELEASE', 'HOTFIX', 'FEATURE', 'BACKUP', name='tagtype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_protected', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['panel_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', 'tag_name', name='uq_version_tag_name')
    )
    
    # Create indexes for tags table
    with op.batch_alter_table('panel_version_tags', schema=None) as batch_op:
        batch_op.create_index('idx_panel_tags_version', ['version_id'], unique=False)
        batch_op.create_index('idx_panel_tags_name', ['tag_name'], unique=False)
        batch_op.create_index('idx_panel_tags_type', ['tag_type'], unique=False)
        batch_op.create_index('idx_panel_tags_protected', ['is_protected'], unique=False)
    
    # Create panel_version_branches table
    op.create_table('panel_version_branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('branch_name', sa.String(length=100), nullable=False),
        sa.Column('parent_version_id', sa.Integer(), nullable=False),
        sa.Column('head_version_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_merged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('merged_at', sa.DateTime(), nullable=True),
        sa.Column('merged_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['head_version_id'], ['panel_versions.id'], ),
        sa.ForeignKeyConstraint(['merged_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['panel_id'], ['saved_panels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_version_id'], ['panel_versions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('panel_id', 'branch_name', name='uq_panel_branch_name')
    )
    
    # Create indexes for branches table
    with op.batch_alter_table('panel_version_branches', schema=None) as batch_op:
        batch_op.create_index('idx_panel_branches_panel', ['panel_id'], unique=False)
        batch_op.create_index('idx_panel_branches_name', ['branch_name'], unique=False)
        batch_op.create_index('idx_panel_branches_active', ['is_active'], unique=False)
        batch_op.create_index('idx_panel_branches_merged', ['is_merged'], unique=False)
    
    # Create panel_version_metadata table for extended version information
    op.create_table('panel_version_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('version_type', sa.Enum('MAIN', 'BRANCH', 'TAG', 'MERGE', name='versiontype'), nullable=False, server_default='MAIN'),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('parent_version_id', sa.Integer(), nullable=True),
        sa.Column('merge_source_version_id', sa.Integer(), nullable=True),
        sa.Column('commit_hash', sa.String(length=64), nullable=True),
        sa.Column('diff_summary', sa.Text(), nullable=True),
        sa.Column('file_changes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lines_added', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lines_removed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retention_priority', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['branch_id'], ['panel_version_branches.id'], ),
        sa.ForeignKeyConstraint(['merge_source_version_id'], ['panel_versions.id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['panel_versions.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['panel_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', name='uq_version_metadata')
    )
    
    # Create indexes for version metadata table
    with op.batch_alter_table('panel_version_metadata', schema=None) as batch_op:
        batch_op.create_index('idx_version_metadata_version', ['version_id'], unique=True)
        batch_op.create_index('idx_version_metadata_type', ['version_type'], unique=False)
        batch_op.create_index('idx_version_metadata_branch', ['branch_id'], unique=False)
        batch_op.create_index('idx_version_metadata_priority', ['retention_priority'], unique=False)
        batch_op.create_index('idx_version_metadata_hash', ['commit_hash'], unique=False)
    
    # Add new columns to existing panel_versions table
    with op.batch_alter_table('panel_versions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_protected', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('retention_priority', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('last_accessed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('size_bytes', sa.BigInteger(), nullable=True))
        batch_op.create_index('idx_panel_versions_protected', ['is_protected'], unique=False)
        batch_op.create_index('idx_panel_versions_priority', ['retention_priority'], unique=False)
        batch_op.create_index('idx_panel_versions_accessed', ['last_accessed_at'], unique=False)
    
    # Create panel_retention_policies table for configurable retention
    op.create_table('panel_retention_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('max_versions', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('backup_retention_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('keep_tagged_versions', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('keep_production_tags', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_cleanup_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_cleanup_at', sa.DateTime(), nullable=True),
        sa.Column('cleanup_frequency_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['panel_id'], ['saved_panels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('panel_id', name='uq_panel_retention_policy')
    )
    
    # Create indexes for retention policies table
    with op.batch_alter_table('panel_retention_policies', schema=None) as batch_op:
        batch_op.create_index('idx_retention_policies_panel', ['panel_id'], unique=True)
        batch_op.create_index('idx_retention_policies_cleanup', ['auto_cleanup_enabled', 'last_cleanup_at'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('panel_retention_policies')
    op.drop_table('panel_version_metadata')
    op.drop_table('panel_version_branches')
    op.drop_table('panel_version_tags')
    
    # Remove columns from panel_versions
    with op.batch_alter_table('panel_versions', schema=None) as batch_op:
        batch_op.drop_index('idx_panel_versions_accessed')
        batch_op.drop_index('idx_panel_versions_priority')
        batch_op.drop_index('idx_panel_versions_protected')
        batch_op.drop_column('size_bytes')
        batch_op.drop_column('access_count')
        batch_op.drop_column('last_accessed_at')
        batch_op.drop_column('retention_priority')
        batch_op.drop_column('is_protected')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS versiontype")
    op.execute("DROP TYPE IF EXISTS tagtype")
