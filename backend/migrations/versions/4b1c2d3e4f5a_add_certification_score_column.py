"""add_certification_score_column

Revision ID: 4b1c2d3e4f5a
Revises: 3a0b1c2d3e4f
Create Date: 2026-08-24

Add certification_score column to analyses table so that certifications
are scored and reported separately from technical skills (see matching
pipeline audit / skill_normalization refactor).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b1c2d3e4f5a'
down_revision: Union[str, None] = '3a0b1c2d3e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analyses', sa.Column('certification_score', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('analyses', 'certification_score')
