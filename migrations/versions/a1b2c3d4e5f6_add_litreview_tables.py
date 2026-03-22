"""add_litreview_tables

Revision ID: a1b2c3d4e5f6
Revises: d24f652d1a59
Create Date: 2026-03-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd24f652d1a59'
branch_labels = None
depends_on = None


def upgrade():
    # Create literature_articles table first (referenced by other tables)
    op.create_table(
        'literature_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pubmed_id', sa.String(length=20), nullable=False),
        sa.Column('pmc_id', sa.String(length=20), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', sa.JSON(), nullable=True),
        sa.Column('journal', sa.String(length=500), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('publication_types', sa.JSON(), nullable=True),
        sa.Column('mesh_terms', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('gene_mentions', sa.JSON(), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('cache_expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pubmed_id', name='uq_literature_articles_pubmed_id'),
    )
    op.create_index('idx_lit_articles_pubmed', 'literature_articles', ['pubmed_id'], unique=False)
    op.create_index('idx_lit_articles_cache_expires', 'literature_articles', ['cache_expires_at'], unique=False)

    # Create literature_searches table
    op.create_table(
        'literature_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_lit_searches_user', 'literature_searches', ['user_id'], unique=False)
    op.create_index('idx_lit_searches_created', 'literature_searches', ['created_at'], unique=False)

    # Create search_results junction table
    op.create_table(
        'search_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['search_id'], ['literature_searches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['literature_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('search_id', 'article_id', name='uq_search_article'),
    )
    op.create_index('idx_search_results_search', 'search_results', ['search_id'], unique=False)
    op.create_index('idx_search_results_article', 'search_results', ['article_id'], unique=False)

    # Create user_article_actions table
    op.create_table(
        'user_article_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('is_saved', sa.Boolean(), nullable=False),
        sa.Column('is_viewed', sa.Boolean(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('first_viewed_at', sa.DateTime(), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(), nullable=True),
        sa.Column('saved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['literature_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'article_id', name='uq_user_article_action'),
    )
    op.create_index('idx_user_article_actions_user', 'user_article_actions', ['user_id'], unique=False)
    op.create_index('idx_user_article_actions_article', 'user_article_actions', ['article_id'], unique=False)
    op.create_index('idx_user_article_actions_saved', 'user_article_actions', ['user_id', 'is_saved'], unique=False)


def downgrade():
    # Drop tables in reverse dependency order
    op.drop_index('idx_user_article_actions_saved', table_name='user_article_actions')
    op.drop_index('idx_user_article_actions_article', table_name='user_article_actions')
    op.drop_index('idx_user_article_actions_user', table_name='user_article_actions')
    op.drop_table('user_article_actions')

    op.drop_index('idx_search_results_article', table_name='search_results')
    op.drop_index('idx_search_results_search', table_name='search_results')
    op.drop_table('search_results')

    op.drop_index('idx_lit_searches_created', table_name='literature_searches')
    op.drop_index('idx_lit_searches_user', table_name='literature_searches')
    op.drop_table('literature_searches')

    op.drop_index('idx_lit_articles_cache_expires', table_name='literature_articles')
    op.drop_index('idx_lit_articles_pubmed', table_name='literature_articles')
    op.drop_table('literature_articles')
