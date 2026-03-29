"""add knowhow last visits

Revision ID: b7c8d9e0f1a2
Revises: a63cbbd8ad61
Create Date: 2026-03-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c8d9e0f1a2'
down_revision = 'a63cbbd8ad61'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('knowhow_last_visits',
        sa.Column('user_id',       sa.Integer(),     nullable=False),
        sa.Column('category_slug', sa.String(64),    nullable=False),
        sa.Column('visited_at',    sa.DateTime(),    nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'category_slug'),
    )


def downgrade():
    op.drop_table('knowhow_last_visits')
