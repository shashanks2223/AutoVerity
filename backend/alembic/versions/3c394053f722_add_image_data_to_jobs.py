"""add_image_data_to_jobs

Revision ID: 3c394053f722
Revises: 9e7c40389d22
Create Date: 2026-08-14 12:00:55.650999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c394053f722'
down_revision: Union[str, Sequence[str], None] = '9e7c40389d22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('image_processing_jobs', sa.Column('image_data', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('image_processing_jobs', 'image_data')
