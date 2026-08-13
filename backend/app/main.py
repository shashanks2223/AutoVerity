import os
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import schemas
from app.config import settings
from app.database import get_db
from app.api.v1.images import router as images_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Media Processing Pipeline Backend API",
    version="1.0.0"
)

# Configure CORS
# Stitch React app runs on VITE_API_BASE_URL=http://localhost:8000 and connects from http://localhost:5173
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=schemas.HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Check the health of the FastAPI application, database, and Redis.
    """
    # Test Database
    try:
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"

    # Test Redis
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    status = "healthy" if database_status == "healthy" and redis_status == "healthy" else "unhealthy"

    return schemas.HealthResponse(
        status=status,
        database=database_status,
        redis=redis_status,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


# Mount routers
app.include_router(images_router, prefix=f"{settings.API_V1_STR}/images", tags=["images"])

# Mount uploads directory to serve stored files statically
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def startup_event():
    # Make sure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Automatically initialize database tables if running SQLite (for local run fallback)
    if "sqlite" in settings.DATABASE_URL:
        from app.database import engine, Base
        from app import models  # noqa
        Base.metadata.create_all(bind=engine)
