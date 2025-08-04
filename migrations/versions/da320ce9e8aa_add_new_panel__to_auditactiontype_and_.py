"""Add new PANEL_* to AuditActionType and PANEL_CREATED to ChangeType enum

Revision ID: da320ce9e8aa
Revises: 64ca2e43ca66
Create Date: 2025-08-03 22:28:23.112709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da320ce9e8aa'
down_revision = '64ca2e43ca66'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to AuditActionType
    op.execute("ALTER TYPE auditactiontype ADD VALUE 'PANEL_CREATE'")
    op.execute("ALTER TYPE auditactiontype ADD VALUE 'PANEL_UPDATE'")
    op.execute("ALTER TYPE auditactiontype ADD VALUE 'PANEL_SHARE'")
    op.execute("ALTER TYPE auditactiontype ADD VALUE 'PANEL_LIST'")
    
    # Add new enum value to ChangeType
    op.execute("ALTER TYPE changetype ADD VALUE 'PANEL_CREATED'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum values in place during downgrade
    # If you need to remove them, you would need to:
    # 1. Create new enum types without these values
    # 2. Update all columns to use new types
    # 3. Drop old enum types
    # 4. Rename new types to original names
    pass
