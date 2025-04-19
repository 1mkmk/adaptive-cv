from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Candidate(Base):
    __tablename__ = "candidate"
    
    id = Column(Integer, primary_key=True, default=1)  # Always use ID 1
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    summary = Column(Text)
    location = Column(String)
    linkedin = Column(String)
    website = Column(String)
    photo = Column(Text)  # Stored as Base64 string or path to image
    skills = Column(Text)  # Stored as JSON string
    experience = Column(Text)  # Stored as JSON string
    education = Column(Text)  # Stored as JSON string
    languages = Column(Text)  # Stored as JSON string
    certifications = Column(Text)  # Stored as JSON string
    projects = Column(Text)  # Stored as JSON string
    references = Column(Text)  # Stored as JSON string
    
    # Extended fields for all templates
    job_title = Column(String)  # Current position/job title
    address = Column(Text)  # Stored as JSON string
    interests = Column(Text)  # Stored as JSON string
    awards = Column(Text)  # Stored as JSON string
    presentations = Column(Text)  # Stored as JSON string
    skill_categories = Column(Text)  # Stored as JSON string
    creativity_levels = Column(Text)  # Stored as JSON string with creativity levels for CV generation
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())