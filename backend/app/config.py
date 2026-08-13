import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Intelligent Media Processing Pipeline"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # DB & Redis Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/media_processor"
    REDIS_URL: str = "redis://localhost:6379/0"
    LOCAL_FALLBACK: bool = False
    GEMINI_API_KEY: str | None = None

    def model_post_init(self, __context):
        if self.LOCAL_FALLBACK:
            self.DATABASE_URL = "sqlite:///media_processor.db"
    
    # File Upload Settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB default
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

    # Image Analysis Thresholds
    BLUR_THRESHOLD: float = 100.0
    BRIGHTNESS_THRESHOLD: float = 70.0
    DUPLICATE_THRESHOLD: int = 4  # Hamming distance <= 4 is duplicate

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
