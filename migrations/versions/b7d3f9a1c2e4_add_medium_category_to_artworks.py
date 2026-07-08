"""add medium_category to artworks

Adds a coarse, indexed `medium_category` bucket derived from the free-text
`medium` field (see app/artworks/medium_categories.py). Backfilled by
scripts/utils/backfill_medium_category.py and kept in sync on save, so the
pondering page can filter by medium group with SQL pagination.

Revision ID: b7d3f9a1c2e4
Revises: 1b2766d5305f
Create Date: 2026-06-28 13:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d3f9a1c2e4'
down_revision = '1b2766d5305f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artworks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('medium_category', sa.String(length=50), nullable=True))
        batch_op.create_index(batch_op.f('ix_artworks_medium_category'), ['medium_category'], unique=False)


def downgrade():
    with op.batch_alter_table('artworks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_artworks_medium_category'))
        batch_op.drop_column('medium_category')
