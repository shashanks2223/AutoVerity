"""Create initial tables

Revision ID: 9e7c40389d22
Revises: 
Create Date: 2026-08-12 18:07:50.687836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e7c40389d22'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create image_processing_jobs table
    op.create_table(
        'image_processing_jobs',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('image_hash', sa.String(length=64), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    # Create indexes on image_processing_jobs
    op.create_index(op.f('ix_image_processing_jobs_status'), 'image_processing_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_image_processing_jobs_created_at'), 'image_processing_jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_image_processing_jobs_image_hash'), 'image_processing_jobs', ['image_hash'], unique=False)

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blur_score', sa.Float(), nullable=False),
        sa.Column('blur_threshold', sa.Float(), nullable=False),
        sa.Column('is_blurry', sa.Boolean(), nullable=False),
        sa.Column('brightness_average', sa.Float(), nullable=False),
        sa.Column('brightness_threshold', sa.Float(), nullable=False),
        sa.Column('is_low_light', sa.Boolean(), nullable=False),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('duplicate_similarity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ocr_raw_text', sa.Text(), nullable=True),
        sa.Column('ocr_normalized_text', sa.Text(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('plate_detected_number', sa.String(length=50), nullable=True),
        sa.Column('plate_format_valid', sa.Boolean(), nullable=True),
        sa.Column('plate_confidence', sa.Float(), nullable=True),
        sa.Column('dimensions_width', sa.Integer(), nullable=False),
        sa.Column('dimensions_height', sa.Integer(), nullable=False),
        sa.Column('dimensions_valid', sa.Boolean(), nullable=False),
        sa.Column('summary_status', sa.String(length=50), nullable=False),
        sa.Column('summary_confidence', sa.Float(), nullable=False),
        sa.Column('summary_issues', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['image_processing_jobs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_analysis_results_job_id'), 'analysis_results', ['job_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_analysis_results_job_id'), table_name='analysis_results')
    op.drop_table('analysis_results')
    op.drop_index(op.f('ix_image_processing_jobs_image_hash'), table_name='image_processing_jobs')
    op.drop_index(op.f('ix_image_processing_jobs_created_at'), table_name='image_processing_jobs')
    op.drop_index(op.f('ix_image_processing_jobs_status'), table_name='image_processing_jobs')
    op.drop_table('image_processing_jobs')

