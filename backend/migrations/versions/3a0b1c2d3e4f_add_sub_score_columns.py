"""add_sub_score_columns_remove_semantic_score

Revision ID: 3a0b1c2d3e4f
Revises: 
Create Date: 2026-08-24

Add soft_skills_score, ai_tools_score, responsibilities_score, location_score columns
to analyses table. Drop legacy semantic_score column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a0b1c2d3e4f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new sub-score columns
    op.add_column('analyses', sa.Column('soft_skills_score', sa.Float(), nullable=True))
    op.add_column('analyses', sa.Column('ai_tools_score', sa.Float(), nullable=True))
    op.add_column('analyses', sa.Column('responsibilities_score', sa.Float(), nullable=True))
    op.add_column('analyses', sa.Column('location_score', sa.Float(), nullable=True))

    # Drop the legacy semantic_score column (was always identical to responsibilities_score)
    op.drop_column('analyses', 'semantic_score')


def downgrade() -> None:
    # Re-add legacy semantic_score column
    op.add_column('analyses', sa.Column('semantic_score', sa.Float(), nullable=True))

    # Drop new sub-score columns
    op.drop_column('analyses', 'location_score')
    op.drop_column('analyses', 'responsibilities_score')
    op.drop_column('analyses', 'ai_tools_score')
    op.drop_column('analyses', 'soft_skills_score')
