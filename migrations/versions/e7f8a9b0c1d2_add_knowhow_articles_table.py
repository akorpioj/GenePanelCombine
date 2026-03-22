"""add knowhow articles table

Revision ID: e7f8a9b0c1d2
Revises: cdf63a989401
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa

revision = 'e7f8a9b0c1d2'
down_revision = 'cdf63a989401'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'knowhow_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowhow_articles_category', 'knowhow_articles', ['category'], unique=False)


def downgrade():
    op.drop_index('ix_knowhow_articles_category', table_name='knowhow_articles')
    op.drop_table('knowhow_articles')
