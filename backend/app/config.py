from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database - SQLite for development, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./thermal_inspection.db"
    
    # JWT
    SECRET_KEY: str = "thermal-inspection-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    UPLOAD_DIR: str = "static/thermal_images"
    PROCESSED_DIR: str = "static/processed_images"
    
    # Thermal Analysis
    AMBIENT_TEMPERATURE: float = 34.0
    POTENTIAL_HOTSPOT_THRESHOLD: float = 20.0  # +20°C above ambient
    CRITICAL_HOTSPOT_THRESHOLD: float = 40.0   # +40°C above ambient
    
    # Email Configuration (for Gmail notifications)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""  # Will be set via env var
    SMTP_PASSWORD: str = ""  # Will be set via env var
    
    # Notification settings
    CHIEF_ENGINEER_EMAIL: str = "tata.power.chief@example.com"  # Replace with actual email
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Production Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Mumbai Salsette Substation Coordinates (for testing)
    SALSETTE_CAMP_LAT: float = 19.1262
    SALSETTE_CAMP_LON: float = 72.8897
    
    class Config:
        env_file = ".env"

settings = Settings() 