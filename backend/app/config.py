"""
Configuration Management for QR Attendance Agent
Handles all environment variables and application settings
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application Settings"""
    
    # Gemini API Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # Airtable Configuration
    AIRTABLE_API_KEY: str
    AIRTABLE_BASE_ID: str
    AIRTABLE_TABLE_NAME: str = "tblZvUKVz1tW0MTvA"
    
    # Application Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Default NSBM Credentials
    DEFAULT_USERNAME: str
    DEFAULT_PASSWORD: str
    
    # Directory Configuration
    QR_CODE_DIR: Path = BASE_DIR / "qr_codes"
    SCREENSHOT_DIR: Path = BASE_DIR / "screenshots"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # QR Code Pattern Configuration
    EVENING_OFFSET: int = 800504  # Difference between morning and evening sessions
    
    # NSBM URL Configuration
    NSBM_BASE_URL: str = "https://students.nsbm.ac.lk/attendence/index.php"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.QR_CODE_DIR.mkdir(parents=True, exist_ok=True)
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


# Initialize settings
settings = Settings()


# Export settings
__all__ = ["settings", "Settings"]