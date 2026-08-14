import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, UUID, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ImageProcessingJob(Base):
    __tablename__ = "image_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    failure_reason = Column(Text, nullable=True)
    image_hash = Column(String(64), nullable=True, index=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    image_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    analysis_result = relationship(
        "AnalysisResult",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("image_processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Blur Detector
    blur_score = Column(Float, nullable=False)
    blur_threshold = Column(Float, nullable=False)
    is_blurry = Column(Boolean, nullable=False)
    
    # Brightness Detector
    brightness_average = Column(Float, nullable=False)
    brightness_threshold = Column(Float, nullable=False)
    is_low_light = Column(Boolean, nullable=False)
    
    # Duplicate Detector
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_similarity = Column(Float, nullable=False, default=0.0)
    
    # OCR
    ocr_raw_text = Column(Text, nullable=True)
    ocr_normalized_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    
    # Vehicle Registration Validation
    plate_detected_number = Column(String(50), nullable=True)
    plate_format_valid = Column(Boolean, nullable=True)
    plate_confidence = Column(Float, nullable=True)
    
    # Image Dimensions
    dimensions_width = Column(Integer, nullable=False)
    dimensions_height = Column(Integer, nullable=False)
    dimensions_valid = Column(Boolean, nullable=False)
    
    # Summary
    summary_status = Column(String(50), nullable=False)  # good, warning, failed
    summary_confidence = Column(Float, nullable=False)
    summary_issues = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ImageProcessingJob", back_populates="analysis_result")
