import os
import uuid
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Response
from sqlalchemy.orm import Session
from PIL import Image
from typing import Optional

from app import models, schemas
from app.database import get_db
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.api.v1.images")

router = APIRouter()


@router.post("/", response_model=schemas.JobCreateResponse, status_code=202)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an image, validate MIME type, file size, extension, and content integrity.
    Create a DB record and queue Celery processing.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    # Validate MIME type
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        logger.warning(f"Rejected upload: Unsupported MIME type {file.content_type}")
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {file.content_type}")

    # Validate file extension
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected upload: Unsupported extension {ext}")
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    # Validate file size (avoid loading unlimited data into memory)
    contents = await file.read(settings.MAX_UPLOAD_SIZE + 1)
    file_size = len(contents)
    if file_size > settings.MAX_UPLOAD_SIZE:
        logger.warning(f"Rejected upload: File size {file_size} exceeds max limit")
        raise HTTPException(status_code=400, detail="File size exceeds maximum upload limit")

    # Validate image content integrity using PIL
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
        # Re-open because verify() closes the file pointer / limits access
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
    except Exception as e:
        logger.warning(f"Rejected upload: Invalid image content. Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid image content or corrupted file")

    # Generate UUID and storage path
    processing_id = uuid.uuid4()
    unique_filename = f"{processing_id}.{ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Save to local storage
    try:
        with open(storage_path, "wb") as f:
            f.write(contents)
        logger.info(f"[{processing_id}] Image stored at {storage_path}")
    except Exception as e:
        logger.error(f"[{processing_id}] Failed to save image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save image to server")

    # Create database record
    try:
        db_job = models.ImageProcessingJob(
            id=processing_id,
            filename=filename,
            mime_type=file.content_type,
            file_size=file_size,
            storage_path=storage_path,
            status="pending",
            width=width,
            height=height,
            image_data=contents
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"[{processing_id}] Database record created successfully")
    except Exception as e:
        logger.error(f"[{processing_id}] Database save failed: {str(e)}")
        if os.path.exists(storage_path):
            os.remove(storage_path)
        raise HTTPException(status_code=500, detail="Database registration failed")

    # Queue asynchronous processing (Celery task)
    try:
        from app.worker import process_image_task
        process_image_task.delay(str(processing_id))
        logger.info(f"[{processing_id}] Job queued in Celery")
    except Exception as e:
        logger.error(f"[{processing_id}] Celery queuing failed: {str(e)}")
        # Since DB is updated and image is saved, we don't fail the request,
        # but mark as failed or let the user know? The requirement says "return immediately".
        # If queue fail, mark job as failed in DB.
        db_job.status = "failed"
        db_job.failure_reason = f"Failed to queue processing job: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to queue processing job")

    return schemas.JobCreateResponse(
        processing_id=processing_id,
        status="pending",
        message="Image accepted for processing"
    )


@router.get("/{processing_id}/status", response_model=schemas.JobStatusResponse)
async def get_image_status(processing_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get job status. Return 404 if not found.
    """
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == processing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return schemas.JobStatusResponse(processing_id=job.id, status=job.status)


@router.get("/{processing_id}/results", response_model=schemas.JobResultsResponse)
async def get_image_results(processing_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get job results. If pending/processing, return 202 indicating not ready.
    """
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == processing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    
    if job.status in ["pending", "processing"]:
        return schemas.JobResultsResponse(
            processing_id=job.id,
            status=job.status,
            message="Results are not ready. Job is still processing."
        )
        
    if job.status == "failed":
        raise HTTPException(status_code=400, detail=f"Job failed. Use failure endpoint for details. Reason: {job.failure_reason}")

    res = job.analysis_result
    if not res:
        raise HTTPException(status_code=400, detail="Analysis results not found for this completed job")

    # Map database models to output schema structure
    image_url = f"{settings.API_V1_STR}/images/{job.id}/image"
    image_info = schemas.ImageInfo(
        filename=job.filename,
        width=job.width,
        height=job.height,
        image_url=image_url
    )
    
    analysis = schemas.DetailedAnalysis(
        blur=schemas.BlurAnalysis(is_blurry=res.is_blurry, score=res.blur_score, threshold=res.blur_threshold),
        brightness=schemas.BrightnessAnalysis(is_low_light=res.is_low_light, average_brightness=res.brightness_average, threshold=res.brightness_threshold),
        duplicate=schemas.DuplicateAnalysis(is_duplicate=res.is_duplicate, similarity=res.duplicate_similarity),
        ocr=schemas.OcrAnalysis(raw_text=res.ocr_raw_text, normalized_text=res.ocr_normalized_text, confidence=res.ocr_confidence),
        vehicle_number=schemas.VehicleNumberAnalysis(detected_number=res.plate_detected_number, format_valid=res.plate_format_valid, confidence=res.plate_confidence),
        dimensions=schemas.DimensionAnalysis(width=res.dimensions_width, height=res.dimensions_height, valid=res.dimensions_valid)
    )
    
    summary = schemas.JobSummary(
        overall_status=res.summary_status,
        confidence=res.summary_confidence,
        issues=res.summary_issues
    )

    return schemas.JobResultsResponse(
        processing_id=job.id,
        status=job.status,
        image=image_info,
        analysis=analysis,
        summary=summary
    )


@router.get("/{processing_id}/image")
async def get_original_image(processing_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve the original binary image bytes directly from PostgreSQL.
    """
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == processing_id).first()
    if not job or not job.image_data:
        raise HTTPException(
            status_code=404,
            detail="Original image not found"
        )
    return Response(content=job.image_data, media_type=job.image_mime_type)



@router.get("/{processing_id}/failure", response_model=schemas.JobFailureResponse)
async def get_image_failure(processing_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get job failure explanation. Return 404 if not found or not in failed state.
    """
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == processing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Job has not failed")
    
    return schemas.JobFailureResponse(
        processing_id=job.id,
        status=job.status,
        failure_reason=job.failure_reason or "Unknown failure"
    )


@router.get("/", response_model=schemas.JobHistoryResponse)
async def get_images_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated history of image processing.
    """
    query = db.query(models.ImageProcessingJob)
    
    if status:
        query = query.filter(models.ImageProcessingJob.status == status)
        
    if search:
        query = query.filter(models.ImageProcessingJob.filename.ilike(f"%{search}%"))
        
    total = query.count()
    offset = (page - 1) * limit
    jobs = query.order_by(models.ImageProcessingJob.created_at.desc()).offset(offset).limit(limit).all()
    
    items = []
    for job in jobs:
        summary = None
        if job.status == "completed" and job.analysis_result:
            summary = schemas.JobSummary(
                overall_status=job.analysis_result.summary_status,
                confidence=job.analysis_result.summary_confidence,
                issues=job.analysis_result.summary_issues
            )
        
        items.append(
            schemas.JobHistoryItem(
                processing_id=job.id,
                filename=job.filename,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                summary=summary
            )
        )
        
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return schemas.JobHistoryResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )
