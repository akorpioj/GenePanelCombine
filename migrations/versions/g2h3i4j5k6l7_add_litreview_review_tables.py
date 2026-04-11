"""add_litreview_review_tables

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Create litreview_review_sessions table
    op.create_table(
        'litreview_review_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ensembl_id', sa.String(length=50), nullable=False),
        sa.Column('gene_symbol', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
        sa.Column('submitted_to_genie', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['search_id'], ['literature_searches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_litreview_sessions_search', 'litreview_review_sessions', ['search_id'])
    op.create_index('idx_litreview_sessions_user', 'litreview_review_sessions', ['user_id'])
    op.create_index('idx_litreview_sessions_status', 'litreview_review_sessions', ['status'])

    # Create litreview_article_categories table
    op.create_table(
        'litreview_article_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('pmid', sa.String(length=20), nullable=False),
        sa.Column('category', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('categorized_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['litreview_review_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['literature_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'article_id', name='uq_session_article_category'),
    )
    op.create_index('idx_litreview_categories_session', 'litreview_article_categories', ['session_id'])
    op.create_index('idx_litreview_categories_article', 'litreview_article_categories', ['article_id'])


def downgrade():
    op.drop_index('idx_litreview_categories_article', table_name='litreview_article_categories')
    op.drop_index('idx_litreview_categories_session', table_name='litreview_article_categories')
    op.drop_table('litreview_article_categories')

    op.drop_index('idx_litreview_sessions_status', table_name='litreview_review_sessions')
    op.drop_index('idx_litreview_sessions_user', table_name='litreview_review_sessions')
    op.drop_index('idx_litreview_sessions_search', table_name='litreview_review_sessions')
    op.drop_table('litreview_review_sessions')
