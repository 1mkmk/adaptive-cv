from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_database, get_db, SessionLocal
from .models.candidate import CandidateProfile
from .models.user import User  # Import User model here to ensure it's loaded before database creation
import importlib.util
import sys
import os
import logging
from dotenv import load_dotenv

# ASCII Logo
ascii_logo = """
     _             _   _            _______      __
    /\\      | |           | | (_)          / ____\\ \\    / /
   /  \\   __| | __ _ _ __ | |_ ___   _____| |     \\ \\  / / 
  / /\\ \\ / _` |/ _` | '_ \\| __| \\ \\ / / _ \\ |      \\ \\/ /  
 / ____ \\ (_| | (_| | |_) | |_| |\\ V /  __/ |____   \\  /   
/_/    \\_\\__,_|\\__,_| .__/ \\__|_| \\_/ \\___|\\_____|   \\/    
                    | |                                    
                    |_|                                    
"""
print(ascii_logo)
print("AdaptiveCV Backend Server Starting...\n")

# Załaduj zmienne środowiskowe z pliku .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)
print(f"Loading .env from: {dotenv_path}")
print(f"OpenAI API Key from .env: {os.getenv('OPENAI_API_KEY', 'Not found')[:5]}...")

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Bardziej permisywna konfiguracja CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # Dla serwera proxy
    "http://127.0.0.1:3001",  # Dla serwera proxy
]

logger.info("Configuring CORS with origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Zmienione na True, aby umożliwić przesyłanie cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Cookie"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=86400,  # 24 godziny cache dla preflight requests
)

# Create the database and tables
create_database()

# User model is now imported at the top
user_model_available = True

# Function to ensure a default guest user and profile exists in local environment
def ensure_default_profile():
    db = SessionLocal()
    try:
        # Check if we're in local environment
        if os.getenv("ENV", "local") == "local" and user_model_available:
            # Try to create a guest user if it doesn't exist
            guest_user = db.query(User).filter(User.email == "guest@example.com").first()
            
            if not guest_user:
                guest_user = User(
                    email="guest@example.com",
                    name="Guest User",
                    is_guest=True,
                    is_active=True,
                    locale="en"
                )
                db.add(guest_user)
                db.commit()
                db.refresh(guest_user)
                logger.info("Created default guest user")
            
            # Check if guest user has a profile
            guest_profile = db.query(CandidateProfile).filter(
                CandidateProfile.user_id == guest_user.id
            ).first()
            
            if not guest_profile:
                # Create a default profile for the guest user
                default_profile = CandidateProfile(
                    user_id=guest_user.id,
                    name="Guest User",
                    email="guest@example.com",
                    phone="",
                    summary="",
                    location="",
                    linkedin="",
                    website="",
                    skills="[]",           # Empty JSON array
                    experience="[]",       # Empty JSON array
                    education="[]",        # Empty JSON array
                    languages="[]",        # Empty JSON array
                    certifications="[]",   # Empty JSON array
                    projects="[]",         # Empty JSON array
                    references="[]",       # Empty JSON array
                    is_default=True
                )
                db.add(default_profile)
                db.commit()
                logger.info(f"Created default profile for guest user (ID: {guest_user.id})")
        else:
            logger.info("Skipping guest user creation (not in local environment or user model unavailable)")
    except Exception as e:
        logger.error(f"Error creating default profile: {str(e)}")
    finally:
        db.close()

# Register startup event to create default profile
@app.on_event("startup")
def startup_db_client():
    ensure_default_profile()

# Import routers safely
def import_router(module_name):
    try:
        return importlib.import_module(f'.routers.{module_name}', 'app').router
    except ImportError as e:
        logger.warning(f"Could not import router {module_name}: {str(e)}")
        return None

# Import core routers
jobs_router = import_router('jobs')
generate_router = import_router('generate')
profile_router = import_router('profile')

# Check if the Google Auth package is available for auth router
google_auth_available = importlib.util.find_spec('google') is not None
auth_router = None

# Only import auth router if Google Auth is available or if we're in local environment
if google_auth_available or os.getenv("ENV", "local") == "local":
    try:
        auth_router = import_router('auth')
        logger.info("Authentication router loaded successfully")
    except Exception as e:
        logger.warning(f"Could not import auth router: {str(e)}")
else:
    logger.warning("Google Auth package not available - Auth features will be limited")

# Include core routers
if jobs_router:
    app.include_router(jobs_router)
if generate_router:
    app.include_router(generate_router)
if profile_router:
    app.include_router(profile_router)
if auth_router:
    app.include_router(auth_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the AdaptiveCV API!",
        "ascii_logo": ascii_logo,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }