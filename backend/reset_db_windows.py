import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to sys.path (Windows-specific)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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
    from app.models.user import User
    from app.models.candidate import CandidateProfile
    from app.models.job import Job
    
    # Import database tools
    from app.database import recreate_database, SessionLocal
    
    logger.info("Resetting database...")
    
    # Recreate the database schema
    recreate_database()
    
    # Create default user and profile
    logger.info("Creating default user and profile...")
    db = SessionLocal()
    try:
        # Create default guest user
        default_user = User(
            email="guest@example.com",
            name="Guest User",
            is_guest=True,
            is_active=True,
            locale="en"
        )
        db.add(default_user)
        db.flush()  # Flush to get the user ID
        
        # Create a default profile for the user
        default_profile = CandidateProfile(
            user_id=default_user.id,
            name="Guest User",
            email="guest@example.com",
            phone="",
            summary="",
            location="",
            linkedin="",
            website="",
            is_default=True,
            skills="[]",
            experience="[]",
            education="[]",
            languages="[]",
            certifications="[]",
            projects="[]",
            references="[]"
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