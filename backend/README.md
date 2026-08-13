# Intelligent Media Processing Pipeline - Backend Service

This repository contains the FastAPI backend for the Intelligent Media Processing Pipeline. The backend handles image uploads, schedules asynchronous media analysis tasks using Celery and Redis, stores status and results in PostgreSQL, and serves clean REST APIs designed for ingestion by a Stitch React frontend.

---

## Technical Stack
- **Web Framework**: FastAPI (Python 3.12+)
- **Asynchronous Task Queue**: Celery + Redis
- **Database**: PostgreSQL (SQLAlchemy ORM + Alembic migrations)
- **Image Processing**: OpenCV, Pillow (PIL), and ImageHash (perceptual hashing)
- **Optical Character Recognition**: Tesseract OCR (`pytesseract`)
- **Validation**: Pydantic v2 (API contracts)
- **Testing**: Pytest

---

## System Architecture

```mermaid
graph TD
    Client[Stitch React Frontend] -- "1. POST /api/v1/images" --> FastAPI[FastAPI Server]
    FastAPI -- "2. Write Job (Status: pending)" --> PostgreSQL[(PostgreSQL)]
    FastAPI -- "3. Queue Job ID" --> Redis[(Redis Broker)]
    FastAPI -- "4. Response (processing_id)" --> Client
    
    Celery[Celery Worker] -- "5. Fetch Task" --> Redis
    Celery -- "6. Set status: processing" --> PostgreSQL
    Celery -- "7. Read Image File" --> Storage[(Shared Storage Volume)]
    Celery -- "8. Execute Quality & OCR Checks" --> Analysis[Analysis Services]
    Celery -- "9. Write Results & Set status: completed/failed" --> PostgreSQL
    
    Client -- "10. GET /api/v1/images/{id}/results" --> FastAPI
    FastAPI -- "11. Fetch Results" --> PostgreSQL
    FastAPI -- "12. Return Results" --> Client
```

### Component Details
1. **FastAPI Web Server**: Handles HTTP request parsing, authentication, routing, CORS headers (allowing Stitch frontend connection), local image storage, and database persistence.
2. **Celery Worker**: Performs background image analysis. If transient connection issues occur, Celery handles retries safely.
3. **Redis Broker**: Serves as the message transport channel between FastAPI and Celery.
4. **PostgreSQL Database**: Holds job records, status flags, perceptual hashes, and quality results.
5. **Shared Storage Volume**: A docker volume `/workspace/uploads` shared between FastAPI and Celery so the worker can read files uploaded by the web server.

---

## Directory Structure

```
backend/
├── alembic/                # Database migrations
├── app/
│   ├── api/                # Route controllers (v1 endpoints)
│   ├── services/           # Decoupled image analysis modules
│   │   ├── blur_detector.py
│   │   ├── brightness_detector.py
│   │   ├── duplicate_detector.py
│   │   ├── image_validator.py
│   │   ├── ocr_service.py
│   │   └── plate_validator.py
│   ├── config.py           # Config settings via pydantic-settings
│   ├── database.py         # DB connection setup
│   ├── models.py           # DB ORM models
│   ├── schemas.py          # API Pydantic response models
│   └── worker.py           # Celery application & task consumer
├── tests/                  # Unit and integration test suites
├── Dockerfile              # Docker container configuration
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Package dependencies
└── README.md               # Developer documentation
```

---

## Setup & Running Guide

### Running via Docker (Recommended)
Make sure Docker is running on your machine, then run:

```bash
docker compose up --build
```

This will automatically spin up PostgreSQL, Redis, FastAPI, and the Celery worker. On startup, FastAPI automatically runs Alembic migrations (`alembic upgrade head`) to construct your tables.

### Running Locally (Development)
1. **Install Tesseract OCR**:
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr libtesseract-dev`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download installer from UB Mannheim and add Tesseract path to environment variable path.
2. **Setup virtual environment & dependencies**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate    # Linux/macOS
   pip install -r requirements.txt
   ```
3. **Spin up local Redis & PostgreSQL** (ensure credentials match `.env`).
4. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```
5. **Start Web Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. **Start Celery Worker**:
   ```bash
   celery -A app.worker.celery_app worker --loglevel=info
   ```

---

## Environment Variables

Copy `.env.example` to `.env` to customize settings:

| Variable | Default Value | Description |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:5173` | The origin allowed to access backend via CORS. |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/media_processor` | PostgreSQL connection URL. |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker and backend connection URL. |
| `UPLOAD_DIR` | `uploads` | Location where uploaded images are saved. |
| `MAX_UPLOAD_SIZE` | `10485760` | Max file upload size in bytes (default 10MB). |
| `BLUR_THRESHOLD` | `100.0` | Laplacian variance below which an image is marked blurry. |
| `BRIGHTNESS_THRESHOLD` | `70.0` | Grayscale pixel average below which it is marked dark. |
| `DUPLICATE_THRESHOLD` | `4` | Max Hamming distance to treat images as duplicates. |
| `GEMINI_API_KEY` | `None` | Gemini API Key for OCR and quality analysis fallback. |

---

## API Endpoints & curl Examples

### 1. Upload Image
- **Endpoint**: `POST /api/v1/images/`
- **Content-Type**: `multipart/form-data`
- **Validation**: Rejects files > 10MB, non-image formats, and corrupt files.
- **Request**:
  ```bash
  curl -X POST -F "file=@/path/to/image.jpg" http://localhost:8000/api/v1/images/
  ```
- **Response** (202 Accepted):
  ```json
  {
    "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
    "status": "pending",
    "message": "Image accepted for processing"
  }
  ```

### 2. Check Job Status
- **Endpoint**: `GET /api/v1/images/{processing_id}/status`
- **Request**:
  ```bash
  curl http://localhost:8000/api/v1/images/9e7c4038-d222-48e0-a7a9-ab80be2c83b0/status
  ```
- **Response** (200 OK):
  ```json
  {
    "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
    "status": "processing"
  }
  ```

### 3. Check Job Results
- **Endpoint**: `GET /api/v1/images/{processing_id}/results`
- **Description**: Returns detailed analysis once completed. If pending/processing, returns message status.
- **Request**:
  ```bash
  curl http://localhost:8000/api/v1/images/9e7c4038-d222-48e0-a7a9-ab80be2c83b0/results
  ```
- **Response (Completed)**:
  ```json
  {
    "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
    "status": "completed",
    "image": {
      "filename": "car.jpg",
      "width": 1920,
      "height": 1080
    },
    "analysis": {
      "blur": {
        "is_blurry": false,
        "score": 250.2,
        "threshold": 100.0
      },
      "brightness": {
        "is_low_light": false,
        "average_brightness": 135.4,
        "threshold": 70.0
      },
      "duplicate": {
        "is_duplicate": false,
        "similarity": 0.0
      },
      "ocr": {
        "raw_text": "KA 01 AB 1234",
        "normalized_text": "KA01AB1234",
        "confidence": 0.82
      },
      "vehicle_number": {
        "detected_number": "KA01AB1234",
        "format_valid": true,
        "confidence": 0.82
      },
      "dimensions": {
        "width": 1920,
        "height": 1080,
        "valid": true
      }
    },
    "summary": {
      "overall_status": "good",
      "confidence": 0.82,
      "issues": []
    }
  }
  ```
- **Response (Pending)**:
  ```json
  {
    "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
    "status": "pending",
    "message": "Results are not ready. Job is still processing."
  }
  ```

### 4. Check Job Failure details
- **Endpoint**: `GET /api/v1/images/{processing_id}/failure`
- **Request**:
  ```bash
  curl http://localhost:8000/api/v1/images/9e7c4038-d222-48e0-a7a9-ab80be2c83b0/failure
  ```
- **Response** (200 OK):
  ```json
  {
    "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
    "status": "failed",
    "failure_reason": "Fatal error: Image file not found at path..."
  }
  ```

### 5. Job History List
- **Endpoint**: `GET /api/v1/images`
- **Query Params**:
  - `page`: default `1`
  - `limit`: default `20`
  - `status`: filter by status (`completed`, `failed`, `pending`, `processing`)
  - `search`: search by original filename
- **Request**:
  ```bash
  curl "http://localhost:8000/api/v1/images/?page=1&limit=20&status=completed&search=car"
  ```
- **Response**:
  ```json
  {
    "items": [
      {
        "processing_id": "9e7c4038-d222-48e0-a7a9-ab80be2c83b0",
        "filename": "car.jpg",
        "status": "completed",
        "created_at": "2026-08-12T13:00:00Z",
        "updated_at": "2026-08-12T13:00:02Z",
        "summary": {
          "overall_status": "good",
          "confidence": 0.82,
          "issues": []
        }
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
  ```

### 6. Health Check
- **Endpoint**: `GET /health`
- **Request**:
  ```bash
  curl http://localhost:8000/health
  ```
- **Response**:
  ```json
  {
    "status": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "timestamp": "2026-08-12T13:00:00.000000Z"
  }
  ```

---

## Stitch Frontend Integration Instructions

The Stitch frontend should connect using the configuration:
```env
# In frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

### CORS Configuration
By default, the backend allows requests from `http://localhost:5173`. If your Stitch React frontend runs on a different port or domain, update the backend `FRONTEND_URL` environment variable to match your frontend origin:
```env
FRONTEND_URL=http://localhost:3000
```
This is critical, otherwise browser preflight OPTIONS requests from Stitch will be blocked.

---

## Testing Guide

Ensure your virtual environment is active, then execute:

```bash
pytest backend/tests -v
```

This runs 20 unit/integration tests covering:
- Health checks (with DB & Redis mock states)
- Upload API validation (sizes, extensions, corrupt content)
- Blur and Brightness scoring algorithms
- License plate formatting and extraction validation
- Duplicate perceptual hashing checks
- Flow status and paginated history routing
- Gemini API fallback configuration and mock responses

---

## Architectural Choices & Design Disclosures

### 1. Duplicate Detection Trade-offs
Duplicate detection utilizes perceptual hashing (`imagehash.phash`) rather than cryptographic hashing (MD5/SHA256). Perceptual hashing converts the luminance structure of the image into a 64-bit value. Visually identical images (even if resized, compressed, or format shifted) generate the same or very close hashes.
- **Hamming Distance**: We compare hashes using Hamming distance. If `distance <= 4` (configurable), they are treated as duplicates.
- **Limitations**: Crops, strong color shifts, or rotations change the perceptual structure and might bypass the duplicate detector. Perceptual hashing can also yield false positives on highly uniform images (like all-white pictures).

### 2. OCR Independence & Resiliency
The OCR service runs Tesseract OCR via `pytesseract`.
- **Failsafe**: OCR can fail if the binary isn't on the system path or if memory is exhausted. We isolated the service calls in a try-catch block. If OCR fails, the system records `None` values and records the issue without halting the rest of the checks (blur, brightness, duplicate checks).
- **Confidence Metrics**: We collect individual word confidences from `image_to_data` and return the average confidence. If no text or confidence structure is parsed, confidence is set to `None` to prevent fabrication of precise ML numbers.

### 3. Indian License Plate Validation Limit
Plate formatting matches standard RTO patterns:
- Standard State plate: `^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$`
- Bharat (BH) Series: `^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$`
- **Limit**: Regex checking only confirms that the parsed text looks like a valid vehicle registration format. It does not contact government databases (VAHAN) to check if the vehicle is active, stolen, or matching the registered description.

### 4. Scalability Considerations
- **Disk IO sharing**: In a multi-worker environment, local uploads might get lost if web and worker run on different physical machines. We use a shared volume for the proof of concept. For production, local storage should be replaced by cloud object stores (like AWS S3 or Google Cloud Storage), returning pre-signed upload URLs.
- **Perceptual Hash Indexing**: Querying duplicates checks all completed records. For millions of records, this O(N) lookup becomes slow. In production, we should index pHashes using BK-trees or Vantage Point trees, or use PgVector for PostgreSQL to execute fast similarity indexing.

### 5. Gemini API Multimodal Fallback
If local OCR fails to extract a valid Indian license plate format or returns empty results, the system can fall back to the Gemini API (`gemini-1.5-flash`) if `GEMINI_API_KEY` is configured in the environment.
- **Multimodal Verification**: Gemini acts as a secondary validator, checking both the license plate text and evaluating whether the image is blurry or dark.
- **Structured JSON Config**: The SDK is configured with `response_mime_type="application/json"` to guarantee the response matches our expected schema format.

---

## AI Usage Disclosure
This backend was created using agentic coding assistance from Antigravity, Google DeepMind's pairs-programming system, following systematic architecture design phases, code structure validation, and automated test-driven iterations.
