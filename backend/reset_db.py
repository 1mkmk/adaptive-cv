import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check for required packages
try:
    import bs4
except ImportError:
    logger.warning("bs4 package not found. Installing bs4...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bs4"])
        logger.info("bs4 installed successfully.")
    except Exception as e:
        logger.error(f"Failed to install bs4: {e}")
        exit(1)

try:
    # First, import models to ensure they're available before we recreate the database
    from app.models.candidate import Candidate
    from app.models.job import Job
    
    # Import database tools
    from app.database import recreate_database, SessionLocal
    
    logger.info("Resetting database...")
    
    # Recreate the database schema
    recreate_database()
    
    # Create default profile
    logger.info("Creating default profile...")
    db = SessionLocal()
    try:
        # Create a default profile
        default_profile = Candidate(
            name="Default User",
            email="user@example.com",
            phone="",
            summary="",
            location="",
            linkedin="",
            website="",
            skills="[]",
            experience="[]",
            education="[]",
            languages="[]",
            certifications="[]",
            projects="[]",
            references="[]",
            creativity_levels="""{"personal_info": 5, "summary": 5, "experience": 5, "education": 5, "skills": 5, "projects": 5, "awards": 5, "presentations": 5, "interests": 5}"""
        )
        db.add(default_profile)
        db.commit()
        logger.info("Default profile created successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating default profile: {e}")
        raise
    finally:
        db.close()
    
    logger.info("Database reset completed successfully")
    
except Exception as e:
    logger.error(f"Error resetting database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)