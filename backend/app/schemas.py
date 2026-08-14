from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, List


# Health Check Schema
class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: str


# Upload Response Schema
class JobCreateResponse(BaseModel):
    processing_id: UUID
    status: str
    message: str


# Status Response Schema
class JobStatusResponse(BaseModel):
    processing_id: UUID
    status: str


# Failure Response Schema
class JobFailureResponse(BaseModel):
    processing_id: UUID
    status: str
    failure_reason: str


# Image Info Schema (part of Results)
class ImageInfo(BaseModel):
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    image_url: Optional[str] = None


# Analysis Sub-schemas
class BlurAnalysis(BaseModel):
    is_blurry: bool
    score: float
    threshold: float


class BrightnessAnalysis(BaseModel):
    is_low_light: bool
    average_brightness: float
    threshold: float


class DuplicateAnalysis(BaseModel):
    is_duplicate: bool
    similarity: float  # Hamming distance or percent similarity


class OcrAnalysis(BaseModel):
    raw_text: Optional[str] = None
    normalized_text: Optional[str] = None
    confidence: Optional[float] = None


class VehicleNumberAnalysis(BaseModel):
    detected_number: Optional[str] = None
    format_valid: bool
    confidence: Optional[float] = None


class DimensionAnalysis(BaseModel):
    width: int
    height: int
    valid: bool


class DetailedAnalysis(BaseModel):
    blur: BlurAnalysis
    brightness: BrightnessAnalysis
    duplicate: DuplicateAnalysis
    ocr: OcrAnalysis
    vehicle_number: VehicleNumberAnalysis
    dimensions: DimensionAnalysis


class JobSummary(BaseModel):
    overall_status: str  # good, warning, failed
    confidence: float
    issues: List[str]


# Final Results Response Schema
class JobResultsResponse(BaseModel):
    processing_id: UUID
    status: str
    image: Optional[ImageInfo] = None
    analysis: Optional[DetailedAnalysis] = None
    summary: Optional[JobSummary] = None
    message: Optional[str] = None  # To use if results are not ready


# History Item Schema
class JobHistoryItem(BaseModel):
    processing_id: UUID
    filename: str
    status: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[JobSummary] = None


# History List Schema
class JobHistoryResponse(BaseModel):
    items: List[JobHistoryItem]
    total: int
    page: int
    limit: int
    pages: int
