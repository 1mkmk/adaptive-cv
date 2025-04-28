import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import sys
import os.path

# Add the project root to sys.path to enable absolute imports
# This assumes the backend folder is directly under the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Define base directories that are needed by other modules
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "assets"))
TEMPLATE_DIR = os.path.abspath(os.path.join(ASSETS_DIR, "templates", "templates_extracted"))

class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "local")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "4f0157c5c84d5a3daa5d0005f5db93c0b2e02b31d0eba048e4aa95337d36189a")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # OpenAI API settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Database settings
    DATABASE_URL: Optional[str] = None  # Loaded dynamically based on environment
    
    # PDF generation settings
    CV_OUTPUT_DIR: str = os.path.abspath(os.path.join("assets", "generated"))
    TEMPLATE_DIR: str = os.path.abspath(os.path.join("assets", "templates", "templates_extracted"))
    
    # Photo settings
    PHOTOS_DIR: str = os.path.abspath(os.path.join("assets", "photos"))
    
    # Default language
    DEFAULT_LANGUAGE: str = "en"
    
    # Available languages
    LANGUAGES: Dict[str, str] = {
        "en": "English",
        "pl": "Polski",
        "de": "Deutsch",
        "fr": "Français",
        "es": "Español"
    }

settings = Settings()

# Dynamically load database configuration based on environment
if settings.ENV == "local":
    from config.local.database import get_db, engine, Base
else:  # cloud
    from config.cloud.database import get_db, engine, Base