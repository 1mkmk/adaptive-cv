from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import jobs, generate, profile
from .database import create_database, get_db, SessionLocal
from .models.candidate import Candidate
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
    "*"
]

logger.info("Configuring CORS with origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # Zmienione na False, żeby uniknąć problemów z preflighted requests
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # 24 godziny cache dla preflight requests
)

# Create the database and tables
create_database()

# Function to ensure a default profile exists
def ensure_default_profile():
    db = SessionLocal()
    try:
        # Check if any profile exists
        existing_profile = db.query(Candidate).first()
        
        # If no profile exists, create a default one
        if not existing_profile:
            default_profile = Candidate(
                name="Default User",
                email="user@example.com",
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
                references="[]"        # Empty JSON array
            )
            db.add(default_profile)
            db.commit()
            logger.info("Created default profile")
        else:
            # Update existing profile with new fields if they're missing
            updated = False
            
            # Check and update new fields
            for field in ['location', 'linkedin', 'website', 'languages', 'certifications', 'projects', 'references']:
                if not hasattr(existing_profile, field) or getattr(existing_profile, field) is None:
                    setattr(existing_profile, field, "[]" if field in ['languages', 'certifications', 'projects', 'references'] else "")
                    updated = True
            
            if updated:
                db.commit()
                logger.info("Updated existing profile with new fields")
    finally:
        db.close()

# Register startup event to create default profile
@app.on_event("startup")
def startup_db_client():
    ensure_default_profile()

# Include routers
app.include_router(jobs.router)
app.include_router(generate.router)
app.include_router(profile.router)  # Renamed from candidates to profile

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the AdaptiveCV API!",
        "ascii_logo": ascii_logo,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }