from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cv = Column(String, nullable=True)  # Generated CV content (base64)
    cv_key = Column(String, nullable=True)  # Unique key for CV files