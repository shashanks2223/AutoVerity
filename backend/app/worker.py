import os
import logging
from datetime import datetime
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.sql import func

from app.config import settings
from app.database import SessionLocal
from app import models

# Configure Celery logging
logger = logging.getLogger("app.worker")
logger.setLevel(logging.INFO)

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

if settings.LOCAL_FALLBACK:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_image_task(self, job_id: str):
    """
    Asynchronous image analysis task.
    Reads the job, validates state, runs individual detectors, performs OCR and validation,
    updates results, handles safe state transitions, and retries on transient errors.
    """
    logger.info(f"[{job_id}] STAGE 1: Task started. Processing UUID initialization...")
    
    import uuid
    if isinstance(job_id, str):
        job_id = uuid.UUID(job_id)
        
    db = SessionLocal()
    try:
        job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"[{job_id}] STAGE 1 ERROR: Job not found in database. Aborting.")
            return

        # Safe status transitions (only pending/processing jobs can be processed)
        if job.status not in ["pending", "processing"]:
            logger.warning(f"[{job_id}] STAGE 1 WARNING: Invalid status transition from {job.status}. Aborting.")
            return

        # Update status to processing
        job.status = "processing"
        job.updated_at = func.now()
        db.commit()
        logger.info(f"[{job_id}] STAGE 1: Job status successfully transitioned to 'processing' in DB.")

        # Lazy imports of detector services to avoid circular imports or early heavy loads
        from app.services.image_validator import ImageValidator
        from app.services.blur_detector import BlurDetector
        from app.services.brightness_detector import BrightnessDetector
        from app.services.duplicate_detector import DuplicateDetector
        from app.services.ocr_service import OcrService
        from app.services.plate_validator import PlateValidator

        # Stage 2: Image loaded
        logger.info(f"[{job_id}] STAGE 2 START: Loading image and checking file path...")
        image_path = job.storage_path
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at path: {image_path}")
        logger.info(f"[{job_id}] STAGE 2: Image file exists. Validating dimensions...")
        width, height, is_valid_dims = ImageValidator.validate(image_path)
        logger.info(f"[{job_id}] STAGE 2 END: Dimensions validated ({width}x{height}, valid={is_valid_dims})")

        # Stage 5: Duplicate detection
        logger.info(f"[{job_id}] STAGE 5 START: Computing perceptual hash for duplicate detection...")
        try:
            p_hash = DuplicateDetector.compute_hash(image_path)
            job.image_hash = p_hash
            db.commit()
            logger.info(f"[{job_id}] STAGE 5: Perceptual hash computed: {p_hash}")
        except Exception as e:
            logger.warning(f"[{job_id}] STAGE 5 WARNING: Duplicate pHash computation failed: {str(e)}")
            p_hash = None

        is_duplicate = False
        similarity_score = 0.0
        if p_hash:
            logger.info(f"[{job_id}] STAGE 5: Searching database for duplicate hashes...")
            duplicate_job_id, similarity_score = DuplicateDetector.find_duplicate(db, job_id, p_hash)
            if duplicate_job_id:
                is_duplicate = True
                logger.info(f"[{job_id}] STAGE 5: Duplicate detected! Match with job: {duplicate_job_id} (Distance: {similarity_score})")
        logger.info(f"[{job_id}] STAGE 5 END: Duplicate detection complete (is_duplicate={is_duplicate})")

        # Stage 3: Blur analysis
        logger.info(f"[{job_id}] STAGE 3 START: Initiating blur analysis...")
        blur_score, is_blurry = BlurDetector.analyze(image_path)
        logger.info(f"[{job_id}] STAGE 3 END: Blur analysis complete (score={blur_score:.1f}, is_blurry={is_blurry})")

        # Stage 4: Brightness analysis
        logger.info(f"[{job_id}] STAGE 4 START: Initiating brightness analysis...")
        brightness_avg, is_low_light = BrightnessDetector.analyze(image_path)
        logger.info(f"[{job_id}] STAGE 4 END: Brightness analysis complete (average={brightness_avg:.1f}, is_low_light={is_low_light})")

        # Stage 6: OCR/Tesseract
        logger.info(f"[{job_id}] STAGE 6 START: Initiating local Tesseract OCR text extraction...")
        ocr_raw_text = None
        ocr_normalized_text = None
        ocr_confidence = None
        try:
            ocr_raw_text, ocr_normalized_text, ocr_confidence = OcrService.extract_text(image_path)
            logger.info(f"[{job_id}] STAGE 6: OCR execution complete. Raw Text parsed: '{ocr_raw_text}', Confidence: {ocr_confidence}")
        except Exception as e:
            logger.warning(f"[{job_id}] STAGE 6 WARNING: OCR service failed non-critically: {str(e)}")

        plate_number = None
        plate_format_valid = False
        plate_confidence = None
        if ocr_normalized_text:
            logger.info(f"[{job_id}] STAGE 6: Validating registration number format...")
            plate_number, plate_format_valid, plate_confidence = PlateValidator.validate(
                ocr_raw_text, ocr_normalized_text, ocr_confidence
            )
            logger.info(f"[{job_id}] STAGE 6: License plate validation results: Number='{plate_number}', Format Valid={plate_format_valid}")
        logger.info(f"[{job_id}] STAGE 6 END: Local OCR & validation completed.")

        # Stage 7: Gemini/AI analysis (if used)
        logger.info(f"[{job_id}] STAGE 7 START: Checking if Gemini API fallback is required...")
        if (not plate_format_valid or not ocr_normalized_text) and settings.GEMINI_API_KEY:
            logger.info(f"[{job_id}] STAGE 7: Local OCR failed to resolve a valid Indian license plate. Invoking Gemini API fallback...")
            try:
                from app.services.gemini_service import GeminiService
                gemini_res = GeminiService.analyze_image(image_path)
                if gemini_res:
                    gemini_plate = gemini_res.get("detected_number")
                    if gemini_plate:
                        ocr_raw_text = gemini_plate
                        ocr_normalized_text = "".join(char for char in gemini_plate if char.isalnum()).upper()
                        ocr_confidence = gemini_res.get("confidence")
                        plate_number, plate_format_valid, plate_confidence = PlateValidator.validate(
                            ocr_raw_text, ocr_normalized_text, ocr_confidence
                        )
                        logger.info(f"[{job_id}] STAGE 7: Gemini Fallback OCR resolved number: '{plate_number}' (Valid format: {plate_format_valid})")
                    
                    if gemini_res.get("is_blurry") and not is_blurry:
                        is_blurry = True
                        logger.info(f"[{job_id}] STAGE 7: Gemini flagged image as blurry.")
                    if gemini_res.get("is_low_light") and not is_low_light:
                        is_low_light = True
                        logger.info(f"[{job_id}] STAGE 7: Gemini flagged image as low light.")
            except Exception as e:
                logger.error(f"[{job_id}] STAGE 7 ERROR: Gemini Fallback service failed: {str(e)}")
        else:
            logger.info(f"[{job_id}] STAGE 7: Gemini fallback skipped (either valid plate resolved locally, or key missing).")
        logger.info(f"[{job_id}] STAGE 7 END: Gemini/AI analysis check finished.")

        # Compile issues list
        issues = []
        if is_blurry:
            issues.append(f"Image is blurry (score: {blur_score:.1f} < threshold: {settings.BLUR_THRESHOLD})")
        if is_low_light:
            issues.append(f"Low light conditions (brightness: {brightness_avg:.1f} < threshold: {settings.BRIGHTNESS_THRESHOLD})")
        if is_duplicate:
            issues.append("Duplicate image detected")
        if not is_valid_dims:
            issues.append(f"Invalid dimensions or aspect ratio ({width}x{height})")
        if ocr_normalized_text and not plate_format_valid:
            issues.append(f"Detected text '{ocr_normalized_text}' does not match standard Indian plate format")
        elif not ocr_normalized_text:
            issues.append("No text detected for registration plate extraction")

        # Determine overall status
        if is_duplicate:
            summary_status = "failed"
        elif is_blurry or is_low_light or not is_valid_dims:
            summary_status = "warning"
        elif plate_format_valid:
            summary_status = "good"
        else:
            summary_status = "warning"

        # Determine overall confidence
        base_confidence = 1.0
        if plate_confidence is not None:
            base_confidence = plate_confidence
        elif ocr_confidence is not None:
            base_confidence = ocr_confidence

        if is_blurry:
            base_confidence *= 0.5
        if is_low_light:
            base_confidence *= 0.8
            
        overall_confidence = round(max(0.0, min(1.0, base_confidence)), 2)

        # Stage 8: Database update
        logger.info(f"[{job_id}] STAGE 8 START: Writing analysis results and status update to DB...")
        res = db.query(models.AnalysisResult).filter(models.AnalysisResult.job_id == job.id).first()
        if not res:
            res = models.AnalysisResult(job_id=job.id)
            db.add(res)

        res.blur_score = blur_score
        res.blur_threshold = settings.BLUR_THRESHOLD
        res.is_blurry = is_blurry
        res.brightness_average = brightness_avg
        res.brightness_threshold = settings.BRIGHTNESS_THRESHOLD
        res.is_low_light = is_low_light
        res.is_duplicate = is_duplicate
        res.duplicate_similarity = similarity_score
        res.ocr_raw_text = ocr_raw_text
        res.ocr_normalized_text = ocr_normalized_text
        res.ocr_confidence = ocr_confidence
        res.plate_detected_number = plate_number
        res.plate_format_valid = plate_format_valid
        res.plate_confidence = plate_confidence
        res.dimensions_width = width
        res.dimensions_height = height
        res.dimensions_valid = is_valid_dims
        res.summary_status = summary_status
        res.summary_confidence = overall_confidence
        res.summary_issues = issues

        # Complete job successfully
        job.status = "completed"
        job.width = width
        job.height = height
        job.updated_at = func.now()
        db.commit()
        logger.info(f"[{job_id}] STAGE 8 END: Database updates successfully committed.")

        # Stage 9: Task completed
        logger.info(f"[{job_id}] STAGE 9: Task completed successfully. Status: {summary_status}")

    except Exception as exc:
        db.rollback()
        logger.error(f"[{job_id}] STAGE ERROR: Processing encountered exception: {str(exc)}")
        
        # Don't retry on non-existent files or other fatal errors
        if isinstance(exc, FileNotFoundError):
            job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.failure_reason = f"Fatal error: {str(exc)}"
                db.commit()
            return

        # Attempt retry for transient exceptions
        try:
            logger.warning(f"[{job_id}] STAGE RETRY: Attempting retry {self.request.retries + 1}/3 due to exception...")
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"[{job_id}] STAGE ERROR: Max retries exceeded. Marking job as failed.")
            job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.failure_reason = f"Processing failed after maximum retries: {str(exc)}"
                db.commit()
        except Exception as retry_exc:
            raise retry_exc
            
    finally:
        db.close()
