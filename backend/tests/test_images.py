import io
import uuid
from PIL import Image
import pytest

from app import models


def create_dummy_image_bytes(format="JPEG", size=(300, 300)):
    """Helper to create valid image bytes in memory."""
    f = io.BytesIO()
    img = Image.new("RGB", size, "white")
    img.save(f, format=format)
    f.seek(0)
    return f.read()


def test_upload_success(client, mock_celery_task):
    """Test successful image upload."""
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/api/v1/images/",
        files={"file": ("car.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 202
    data = response.json()
    assert "processing_id" in data
    assert data["status"] == "pending"
    assert "message" in data
    
    # Verify Celery delay was called
    mock_celery_task.assert_called_once_with(data["processing_id"])


def test_upload_invalid_mime(client):
    """Test rejection of invalid MIME type."""
    response = client.post(
        "/api/v1/images/",
        files={"file": ("test.txt", b"some random text contents", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported MIME type" in response.json()["detail"]


def test_upload_invalid_extension(client):
    """Test rejection of invalid file extension."""
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/api/v1/images/",
        files={"file": ("car.pdf", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_corrupt_image(client):
    """Test rejection of corrupted image contents."""
    response = client.post(
        "/api/v1/images/",
        files={"file": ("car.jpg", b"corrupt bytes that cannot be read by PIL", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Invalid image content" in response.json()["detail"]


def test_get_status_404(client):
    """Test 404 response for non-existent processing ID."""
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/images/{random_uuid}/status")
    assert response.status_code == 404
    assert "Processing job not found" in response.json()["detail"]


def test_get_status_pending(client, db):
    """Test status query on a pending job."""
    job_id = uuid.uuid4()
    job = models.ImageProcessingJob(
        id=job_id,
        filename="car.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        storage_path="uploads/dummy.jpg",
        status="pending"
    )
    db.add(job)
    db.commit()

    response = client.get(f"/api/v1/images/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["processing_id"] == str(job_id)
    assert data["status"] == "pending"


def test_get_results_not_ready(client, db):
    """Test results query when job is not yet completed."""
    job_id = uuid.uuid4()
    job = models.ImageProcessingJob(
        id=job_id,
        filename="car.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        storage_path="uploads/dummy.jpg",
        status="processing"
    )
    db.add(job)
    db.commit()

    response = client.get(f"/api/v1/images/{job_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["processing_id"] == str(job_id)
    assert data["status"] == "processing"
    assert "not ready" in data["message"].lower()
    assert data["analysis"] is None


def test_get_results_success(client, db):
    """Test results query for a completed job."""
    job_id = uuid.uuid4()
    job = models.ImageProcessingJob(
        id=job_id,
        filename="car.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        storage_path="uploads/dummy.jpg",
        status="completed",
        width=1920,
        height=1080
    )
    db.add(job)
    db.flush()

    res = models.AnalysisResult(
        job_id=job_id,
        blur_score=250.2,
        blur_threshold=100.0,
        is_blurry=False,
        brightness_average=135.4,
        brightness_threshold=70.0,
        is_low_light=False,
        is_duplicate=False,
        duplicate_similarity=0.0,
        ocr_raw_text="KA 01 AB 1234",
        ocr_normalized_text="KA01AB1234",
        ocr_confidence=0.82,
        plate_detected_number="KA01AB1234",
        plate_format_valid=True,
        plate_confidence=0.82,
        dimensions_width=1920,
        dimensions_height=1080,
        dimensions_valid=True,
        summary_status="good",
        summary_confidence=0.82,
        summary_issues=[]
    )
    db.add(res)
    db.commit()

    response = client.get(f"/api/v1/images/{job_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["processing_id"] == str(job_id)
    assert data["status"] == "completed"
    assert data["image"]["filename"] == "car.jpg"
    assert data["image"]["width"] == 1920
    assert data["analysis"]["blur"]["score"] == 250.2
    assert data["analysis"]["ocr"]["normalized_text"] == "KA01AB1234"
    assert data["analysis"]["vehicle_number"]["format_valid"] is True
    assert data["summary"]["overall_status"] == "good"


def test_get_failure_details(client, db):
    """Test failure endpoint."""
    job_id = uuid.uuid4()
    
    # 1. Test 404 for missing job
    response = client.get(f"/api/v1/images/{job_id}/failure")
    assert response.status_code == 404

    # 2. Test 400 for non-failed job
    job = models.ImageProcessingJob(
        id=job_id,
        filename="car.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        storage_path="uploads/dummy.jpg",
        status="completed"
    )
    db.add(job)
    db.commit()
    response = client.get(f"/api/v1/images/{job_id}/failure")
    assert response.status_code == 400

    # 3. Test successful failure detail retrieval
    job.status = "failed"
    job.failure_reason = "Corrupt image format"
    db.commit()
    response = client.get(f"/api/v1/images/{job_id}/failure")
    assert response.status_code == 200
    data = response.json()
    assert data["processing_id"] == str(job_id)
    assert data["status"] == "failed"
    assert data["failure_reason"] == "Corrupt image format"


def test_history_list(client, db):
    """Test history API with pagination and filters."""
    # Seed 3 jobs
    for i in range(3):
        job = models.ImageProcessingJob(
            id=uuid.uuid4(),
            filename=f"image_{i}.jpg",
            mime_type="image/jpeg",
            file_size=2048,
            storage_path=f"uploads/dummy_{i}.jpg",
            status="completed" if i < 2 else "failed"
        )
        db.add(job)
    db.commit()

    # Get history
    response = client.get("/api/v1/images/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["pages"] == 1

    # Filter status
    response = client.get("/api/v1/images/?status=failed")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "failed"

    # Search query
    response = client.get("/api/v1/images/?search=image_1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["filename"] == "image_1.jpg"


def test_upload_and_results_uppercase_extension(client, mock_celery_task, db):
    """Test upload and results retrieval of an image with an uppercase extension,
    verifying dimensions and file info mapping."""
    img_bytes = create_dummy_image_bytes(format="JPEG", size=(180, 180))
    # Post image with uppercase extension
    response = client.post(
        "/api/v1/images/",
        files={"file": ("vehicle_image.JPG", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 202
    data = response.json()
    job_id = data["processing_id"]
    
    # Retrieve job from DB to confirm initial dimensions were recorded
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == uuid.UUID(job_id)).first()
    assert job is not None
    assert job.width == 180
    assert job.height == 180
    assert job.filename == "vehicle_image.JPG"
    # Ensure lowercase extension on disk
    assert job.storage_path.endswith(".jpg")
    
    # Simulate worker update
    job.status = "completed"
    res = models.AnalysisResult(
        job_id=job.id,
        blur_score=150.0,
        blur_threshold=100.0,
        is_blurry=False,
        brightness_average=100.0,
        brightness_threshold=70.0,
        is_low_light=False,
        is_duplicate=False,
        duplicate_similarity=0.0,
        ocr_raw_text="MH12AB1234",
        ocr_normalized_text="MH12AB1234",
        ocr_confidence=0.9,
        plate_detected_number="MH12AB1234",
        plate_format_valid=True,
        plate_confidence=0.9,
        dimensions_width=180,
        dimensions_height=180,
        dimensions_valid=False,
        summary_status="warning",
        summary_confidence=0.9,
        summary_issues=["Invalid dimensions or aspect ratio (180x180)"]
    )
    db.add(res)
    db.commit()
    
    # Query API results
    response_results = client.get(f"/api/v1/images/{job_id}/results")
    assert response_results.status_code == 200
    results_data = response_results.json()
    
    # Verify results data properties
    assert results_data["image"]["filename"] == "vehicle_image.JPG"
    assert results_data["image"]["width"] == 180
    assert results_data["image"]["height"] == 180
    assert results_data["analysis"]["dimensions"]["width"] == 180
    assert results_data["analysis"]["dimensions"]["height"] == 180
    assert results_data["analysis"]["dimensions"]["valid"] is False


def test_image_binary_data_storage_and_serving(client, db, mock_celery_task):
    """Test PostgreSQL LargeBinary image storage and serving endpoint."""
    img_bytes = create_dummy_image_bytes(format="PNG")
    
    # A. Upload an image
    response = client.post(
        "/api/v1/images/",
        files={"file": ("test2.png", img_bytes, "image/png")}
    )
    assert response.status_code == 202
    data = response.json()
    job_id = data["processing_id"]
    
    # B. Verify image_data, filename, and mime_type is stored in DB
    job = db.query(models.ImageProcessingJob).filter(models.ImageProcessingJob.id == uuid.UUID(job_id)).first()
    assert job is not None
    assert job.image_data == img_bytes
    assert job.filename == "test2.png"
    assert job.mime_type == "image/png"
    assert job.image_filename == "test2.png"
    assert job.image_mime_type == "image/png"
    
    # E. Verify GET /api/v1/images/{job_id}/image returns 200 OK
    serving_response = client.get(f"/api/v1/images/{job_id}/image")
    assert serving_response.status_code == 200
    
    # F. Verify Content-Type is correct
    assert serving_response.headers["content-type"] == "image/png"
    
    # G. Verify returned response bytes exactly match the uploaded image bytes
    assert serving_response.content == img_bytes
    
    # H. Verify missing image returns 404
    non_existent_uuid = str(uuid.uuid4())
    missing_response = client.get(f"/api/v1/images/{non_existent_uuid}/image")
    assert missing_response.status_code == 404


