"""add is_draft to knowhow_articles

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-03-29 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'knowhow_articles',
        sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade():
    op.drop_column('knowhow_articles', 'is_draft')
