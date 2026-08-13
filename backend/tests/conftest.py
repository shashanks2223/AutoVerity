import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
import os
import shutil

from app.database import Base, get_db
from app import models  # Ensure models are loaded to register schemas
from app.main import app
from app.config import settings

# Use SQLite file-based database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Ensure upload directory exists during testing, and cleanup after."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Cleanup uploaded files after test session
    if os.path.exists(settings.UPLOAD_DIR) and settings.UPLOAD_DIR == "uploads_test":
        shutil.rmtree(settings.UPLOAD_DIR)
    # Cleanup test database file
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except Exception:
            pass


@pytest.fixture(scope="function")
def db():
    """Create in-memory SQLite tables and yield a session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Override FastAPI get_db dependency and yield TestClient."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_celery_task(monkeypatch):
    """Mock Celery process_image_task.delay call."""
    mock_delay = MagicMock()
    try:
        from app.worker import process_image_task
        monkeypatch.setattr(process_image_task, "delay", mock_delay)
    except Exception:
        pass
    return mock_delay
