import os
import sys
import uuid
from PIL import Image, ImageDraw
from unittest.mock import MagicMock, patch

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Set local fallback to True and mock Gemini Key for verification
os.environ["LOCAL_FALLBACK"] = "True"
os.environ["GEMINI_API_KEY"] = "fake_verification_api_key"

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models
from app.worker import process_image_task


def setup_verification_db():
    """Create database tables in media_processor.db if they don't exist."""
    print("[Verification] Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)


def create_dummy_image(path):
    """Generate a simple gray image."""
    img = Image.new("RGB", (300, 300), "gray")
    img.save(path)
    print(f"[Verification] Created temporary test image at: {path}")


@patch("google.generativeai.GenerativeModel")
@patch("app.services.ocr_service.OcrService.extract_text")
def run_verification(mock_ocr_extract, mock_model_class):
    """Run fallback integration check."""
    setup_verification_db()
    
    # 1. Setup local OCR mock to return empty (simulating local failure/missing Tesseract)
    mock_ocr_extract.return_value = (None, None, None)
    
    # 2. Setup Gemini mock response with JSON matching expected layout
    mock_response = MagicMock()
    mock_response.text = (
        '{\n'
        '  "detected_number": "KA01AB1234",\n'
        '  "is_blurry": true,\n'
        '  "is_low_light": true,\n'
        '  "confidence": 0.95,\n'
        '  "issues": ["Image blurry", "Low light conditions"]\n'
        '}'
    )
    
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance
    
    # 3. Create dummy image file and save initial pending record to DB
    job_id = uuid.uuid4()
    test_image_path = "fallback_test.jpg"
    create_dummy_image(test_image_path)
    
    db = SessionLocal()
    try:
        # Create database job
        db_job = models.ImageProcessingJob(
            id=job_id,
            filename="car_failed_ocr.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            storage_path=test_image_path,
            status="pending"
        )
        db.add(db_job)
        db.commit()
        print(f"[Verification] Registered processing job in DB with ID: {job_id}")
        
        # 4. Invoke the Celery task synchronously
        print("[Verification] Invoking process_image_task Celery function...")
        process_image_task(str(job_id))
        
        # 5. Retrieve result and verify fields
        db.refresh(db_job)
        print("\n================ Verification Results ================")
        print(f"Job Status: {db_job.status}")
        print(f"Computed Image Hash: {db_job.image_hash}")
        
        analysis = db_job.analysis_result
        if analysis:
            print(f"Local OCR text (mocked to fail): {analysis.ocr_raw_text}")
            print(f"Gemini Fallback detected plate: {analysis.plate_detected_number}")
            print(f"Gemini Fallback plate format valid: {analysis.plate_format_valid}")
            print(f"Gemini Fallback plate confidence: {analysis.plate_confidence}")
            print(f"Image marked Blurry: {analysis.is_blurry}")
            print(f"Image marked Low light: {analysis.is_low_light}")
            print(f"Summary status: {analysis.summary_status}")
            print(f"Summary issues: {analysis.summary_issues}")
            
            # Assertions to confirm fallback integration logic is correct
            assert analysis.plate_detected_number == "KA01AB1234"
            assert analysis.plate_format_valid is True
            assert analysis.is_blurry is True
            assert analysis.is_low_light is True
            print("======================================================")
            print("\n[SUCCESS] The Gemini API fallback integration is verified and working perfectly!")
        else:
            print("\n[ERROR] Analysis result record was not created.")
            
    finally:
        # Cleanup DB record and files
        db.rollback()
        # Delete job
        job_to_del = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == job_id).first()
        if job_to_del:
            db.delete(job_to_del)
            db.commit()
        db.close()
        
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print("[Verification] Temporary test image removed.")


if __name__ == "__main__":
    run_verification()
