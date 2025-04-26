import os
import logging
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load database configuration based on environment
ENV = os.getenv("ENV", "local")

if ENV == "local":
    # SQLite configuration for local development
    logger.info("Using SQLite database for local environment")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./adaptive_cv.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration for cloud deployment
    logger.info("Using PostgreSQL database for cloud environment")
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://adaptive_cv:adaptive_cv_secure_password@db:5432/adaptive_cv")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def create_database():
    """Create all tables in the database"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise e

def recreate_database():
    """Drop all tables and recreate them"""
    try:
        logger.info("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped")
        create_database()
    except Exception as e:
        logger.error(f"Error recreating database tables: {e}")
        raise e

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()