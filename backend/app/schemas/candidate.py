from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime

class ExperienceItem(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    current: bool = False
    description: str

class EducationItem(BaseModel):
    institution: str
    degree: str
    field: str
    start_date: str
    end_date: Optional[str] = None
    current: bool = False

class LanguageItem(BaseModel):
    name: str
    level: str

class CertificationItem(BaseModel):
    name: str
    issuer: str
    date: str
    url: Optional[str] = None

class ProjectItem(BaseModel):
    name: str
    description: str
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ReferenceItem(BaseModel):
    name: str
    position: str
    company: str
    contact: str

class AddressItem(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str

class InterestItem(BaseModel):
    type: Literal['professional', 'personal']
    description: str

class AwardItem(BaseModel):
    title: str
    date: str
    issuer: str
    description: Optional[str] = None

class PresentationItem(BaseModel):
    title: str
    date: str
    venue: str
    description: Optional[str] = None

class SkillCategoryItem(BaseModel):
    name: str
    skills: List[str] = []

class CandidateProfile(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    photo: Optional[str] = None  # Base64 encoded image data
    skills: List[str] = []
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    languages: Optional[List[LanguageItem]] = []
    certifications: Optional[List[CertificationItem]] = []
    projects: Optional[List[ProjectItem]] = []
    references: Optional[List[ReferenceItem]] = []
    # Extended fields
    job_title: Optional[str] = None
    address: Optional[AddressItem] = None
    interests: Optional[List[InterestItem]] = []
    awards: Optional[List[AwardItem]] = []
    presentations: Optional[List[PresentationItem]] = []
    skill_categories: Optional[List[SkillCategoryItem]] = []
    creativity_levels: Optional[Dict[str, int]] = None

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    photo: Optional[str] = None  # Base64 encoded image data
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    languages: Optional[List[LanguageItem]] = None
    certifications: Optional[List[CertificationItem]] = None
    projects: Optional[List[ProjectItem]] = None
    references: Optional[List[ReferenceItem]] = None
    # Extended fields
    job_title: Optional[str] = None
    address: Optional[AddressItem] = None
    interests: Optional[List[InterestItem]] = None
    awards: Optional[List[AwardItem]] = None
    presentations: Optional[List[PresentationItem]] = None
    skill_categories: Optional[List[SkillCategoryItem]] = None
    creativity_levels: Optional[Dict[str, int]] = None

class CandidateResponse(CandidateProfile):
    id: Optional[int] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProfileGenerationPrompt(BaseModel):
    prompt: str
    creativity_levels: Dict[str, int] = Field(
        default_factory=lambda: {
            "personal_info": 5,
            "summary": 5,
            "experience": 5,
            "education": 5,
            "skills": 5,
            "projects": 5,
            "awards": 5,
            "presentations": 5,
            "interests": 5
        },
        description="Creativity levels for each section, from 0 (factual) to 10 (creative)"
    )
    job_description: Optional[str] = None