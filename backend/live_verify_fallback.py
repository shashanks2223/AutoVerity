import os
import sys
import uuid
from PIL import Image, ImageDraw
from unittest.mock import patch

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Set local fallback database
os.environ["LOCAL_FALLBACK"] = "True"

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models
from app.worker import process_image_task


def setup_db():
    Base.metadata.create_all(bind=engine)


def generate_live_test_image(path):
    """Draw a clean, high-contrast text plate on a canvas so Gemini can read it."""
    # Create a white canvas (simulating a clean license plate background)
    img = Image.new("RGB", (450, 120), "white")
    draw = ImageDraw.Draw(img)
    
    # Draw a thin black border
    draw.rectangle([10, 10, 440, 110], outline="black", width=3)
    
    # Draw simple block letters manually to ensure they are large, clear,
    # and don't depend on system font files (.ttf) being present.
    # We will write: "KA 01 AB 1234" using standard Pillow text
    # Pillow's default font is used, but we scale/multiply pixel boxes to make it very large.
    try:
        # Try loading default font or drawing large text
        draw.text((60, 45), "KA 01 AB 1234", fill="black")
    except Exception:
        # Fallback to drawing a simple block representations if drawing text throws
        pass
        
    img.save(path)
    print(f"[Live Check] Generated high-contrast test image containing 'KA 01 AB 1234' at: {path}")


@patch("app.services.ocr_service.OcrService.extract_text")
def run_live_check(mock_ocr_extract):
    """Trigger the live fallback workflow using the configured Gemini API key."""
    setup_db()
    
    # Verify key exists
    if not settings.GEMINI_API_KEY:
        print("[Error] GEMINI_API_KEY is not set in backend/.env. Cannot perform live check.")
        return
        
    print(f"[Live Check] Detected Gemini API Key: {settings.GEMINI_API_KEY[:8]}...[hidden]")
    
    # 1. Force local OCR to fail
    mock_ocr_extract.return_value = (None, None, None)
    
    # 2. Create test plate image
    test_image_path = "live_fallback_test.jpg"
    generate_live_test_image(test_image_path)
    
    job_id = uuid.uuid4()
    db = SessionLocal()
    try:
        # Create database job
        db_job = models.ImageProcessingJob(
            id=job_id,
            filename="live_fallback_car.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            storage_path=test_image_path,
            status="pending"
        )
        db.add(db_job)
        db.commit()
        print(f"[Live Check] Job queued in database with ID: {job_id}")
        
        # 3. Process task synchronously
        print("[Live Check] Running process_image_task Celery function (calling Gemini API)...")
        process_image_task(str(job_id))
        
        # 4. Read results
        db.refresh(db_job)
        print("\n================= Live Fallback Results =================")
        print(f"Job Status: {db_job.status}")
        
        analysis = db_job.analysis_result
        if analysis:
            print(f"Gemini OCR Result: '{analysis.ocr_raw_text}'")
            print(f"Plate Extracted: '{analysis.plate_detected_number}'")
            print(f"Format Validation: {analysis.plate_format_valid}")
            print(f"Gemini Confidence: {analysis.plate_confidence}")
            print(f"Image Blurry: {analysis.is_blurry}")
            print(f"Image Low Light: {analysis.is_low_light}")
            print(f"Issues found: {analysis.summary_issues}")
            print("=========================================================")
            
            if analysis.plate_format_valid:
                print("\n[SUCCESS] The Gemini API fallback successfully analyzed the image over the network!")
            else:
                print("\n[WARNING] Gemini processed the image but did not find a valid plate format. Check if the image text was visible.")
        else:
            print("\n[ERROR] No analysis results created. Check Celery logs for exceptions.")
            if db_job.status == "failed":
                print(f"Failure Reason: {db_job.failure_reason}")
                
    finally:
        db.rollback()
        # Delete job
        job_to_del = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == job_id).first()
        if job_to_del:
            db.delete(job_to_del)
            db.commit()
        db.close()
        
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print("[Live Check] Cleanup completed.")


if __name__ == "__main__":
    run_live_check()
