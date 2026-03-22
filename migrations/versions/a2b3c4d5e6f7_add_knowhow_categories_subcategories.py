"""add knowhow categories and subcategories

Revision ID: a2b3c4d5e6f7
Revises: e7f8a9b0c1d2
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b3c4d5e6f7'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. knowhow_categories
    op.create_table(
        'knowhow_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('color', sa.String(length=32), nullable=False, server_default='#0369a1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowhow_categories_slug', 'knowhow_categories', ['slug'], unique=True)

    # 2. knowhow_subcategories
    op.create_table(
        'knowhow_subcategories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['knowhow_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowhow_subcategories_category_id', 'knowhow_subcategories', ['category_id'])

    # 3. Add subcategory_id to knowhow_links
    op.add_column('knowhow_links', sa.Column('subcategory_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_knowhow_links_subcategory',
        'knowhow_links', 'knowhow_subcategories',
        ['subcategory_id'], ['id'],
        ondelete='SET NULL'
    )

    # 4. Add subcategory_id to knowhow_articles
    op.add_column('knowhow_articles', sa.Column('subcategory_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_knowhow_articles_subcategory',
        'knowhow_articles', 'knowhow_subcategories',
        ['subcategory_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_knowhow_articles_subcategory', 'knowhow_articles', type_='foreignkey')
    op.drop_column('knowhow_articles', 'subcategory_id')
    op.drop_constraint('fk_knowhow_links_subcategory', 'knowhow_links', type_='foreignkey')
    op.drop_column('knowhow_links', 'subcategory_id')
    op.drop_index('ix_knowhow_subcategories_category_id', table_name='knowhow_subcategories')
    op.drop_table('knowhow_subcategories')
    op.drop_index('ix_knowhow_categories_slug', table_name='knowhow_categories')
    op.drop_table('knowhow_categories')
