from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    description: str
    source_url: Optional[str] = None
    
class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    created_at: datetime
    cv: Optional[str] = None
    cv_key: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    cv: Optional[str] = None
    cv_key: Optional[str] = None