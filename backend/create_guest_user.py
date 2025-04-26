import os
import sys
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_guest_user():
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if guest user already exists
        existing_guest = db.query(User).filter(User.email == "guest@example.com").first()
        
        if existing_guest:
            logger.info("Guest user already exists, skipping creation")
            return
        
        # Create guest user
        logger.info("Creating guest user")
        guest_user = User(
            email="guest@example.com",
            name="Guest User",
            is_guest=True,
            is_active=True,
            locale="en"
        )
        
        db.add(guest_user)
        db.commit()
        logger.info("Guest user created successfully")
        
    except Exception as e:
        logger.error(f"Error creating guest user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Create guest user
        create_guest_user()
        
        logger.info("Initial setup completed successfully")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)