"""add og columns to knowhow_links

Revision ID: f1a2b3c4d5e6
Revises: c1d2e3f4a5b6
Create Date: 2026-03-29 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('knowhow_links', schema=None) as batch_op:
        batch_op.add_column(sa.Column('og_title',       sa.String(length=256),  nullable=True))
        batch_op.add_column(sa.Column('og_description', sa.String(length=512),  nullable=True))
        batch_op.add_column(sa.Column('og_image_url',   sa.String(length=2048), nullable=True))


def downgrade():
    with op.batch_alter_table('knowhow_links', schema=None) as batch_op:
        batch_op.drop_column('og_image_url')
        batch_op.drop_column('og_description')
        batch_op.drop_column('og_title')
