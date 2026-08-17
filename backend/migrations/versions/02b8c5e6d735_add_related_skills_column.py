"""add related skills column

Revision ID: 02b8c5e6d735
Revises: 01a9b4f5b824
Create Date: 2024-03-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '02b8c5e6d735'
down_revision: Union[str, None] = '01a9b4f5b824'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analyses', sa.Column('related_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('analyses', 'related_skills')
