"""add_export_template_audit_types

Revision ID: b413fb2acd82
Revises: 9227e34bde83
Create Date: 2025-10-13 10:59:24.949805

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b413fb2acd82'
down_revision = '9227e34bde83'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to AuditActionType enum for export template operations
    # PostgreSQL requires using raw SQL to add enum values
    op.execute("ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_CREATE'")
    op.execute("ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_UPDATE'")
    op.execute("ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_DELETE'")


def downgrade():
    # Note: PostgreSQL does not support removing enum values directly
    # The enum values will remain in the database if downgraded
    # This is a PostgreSQL limitation - enum values cannot be removed
    # If you need to truly remove them, you would need to:
    # 1. Create a new enum type without these values
    # 2. Alter the column to use the new type
    # 3. Drop the old enum type
    # This is complex and risky, so we leave the values in place
    pass
