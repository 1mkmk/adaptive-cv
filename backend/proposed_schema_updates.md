# Proposed Schema Updates for Full Template Support

To fully support both the FAANG and Wenneker CV templates, the following updates to the schema are proposed:

## SQLAlchemy Model Updates (in `candidate.py`)

```python
# Add these new fields to the Candidate class
class Candidate(Base):
    # Existing fields...
    # ...
    
    # New fields for template support
    job_title = Column(String)  # Current position/job title
    address = Column(Text)  # JSON string with structured address
    interests = Column(Text)  # JSON string with professional and personal interests
    awards = Column(Text)  # JSON string with awards and achievements
    presentations = Column(Text)  # JSON string with presentations/talks
    skill_categories = Column(Text)  # JSON string with categorized skills
```

## Pydantic Schema Updates (in `candidate.py`)

```python
# New model classes
class Address(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str

class Interest(BaseModel):
    type: str  # 'professional' or 'personal'
    description: str

class Award(BaseModel):
    title: str
    date: str
    issuer: str
    description: Optional[str] = None

class Presentation(BaseModel):
    title: str
    date: str
    venue: str
    description: Optional[str] = None

class SkillCategory(BaseModel):
    name: str
    skills: List[str]

# Update CandidateProfile model
class CandidateProfile(BaseModel):
    # Existing fields...
    # ...
    
    # New fields for template support
    job_title: Optional[str] = None
    address: Optional[Address] = None
    interests: Optional[List[Interest]] = []
    awards: Optional[List[Award]] = []
    presentations: Optional[List[Presentation]] = []
    skill_categories: Optional[List[SkillCategory]] = []

# Update CandidateUpdate model similarly
class CandidateUpdate(BaseModel):
    # Existing fields...
    # ...
    
    # New fields for template support
    job_title: Optional[str] = None
    address: Optional[Address] = None
    interests: Optional[List[Interest]] = None
    awards: Optional[List[Award]] = None
    presentations: Optional[List[Presentation]] = None
    skill_categories: Optional[List[SkillCategory]] = None
```

## Backend Endpoint Updates (in `profile.py` router)

The existing `/profile` endpoint would need to be updated to handle the new fields in both GET and PUT requests. The JSON serialization and deserialization would need to accommodate the new nested structures.

```python
@router.get("", response_model=CandidateResponse)
def get_profile(db: Session = Depends(get_db)):
    # Existing code...
    
    # Add deserialization of new JSON fields
    if candidate.address:
        candidate_dict["address"] = json.loads(candidate.address)
    if candidate.interests:
        candidate_dict["interests"] = json.loads(candidate.interests)
    if candidate.awards:
        candidate_dict["awards"] = json.loads(candidate.awards)
    if candidate.presentations:
        candidate_dict["presentations"] = json.loads(candidate.presentations)
    if candidate.skill_categories:
        candidate_dict["skill_categories"] = json.loads(candidate.skill_categories)
    
    return candidate_dict

@router.put("", response_model=CandidateResponse)
def update_profile(profile: CandidateUpdate, db: Session = Depends(get_db)):
    # Existing code...
    
    # Add serialization for new fields
    if profile.address is not None:
        candidate.address = json.dumps(profile.address.dict())
    if profile.interests is not None:
        candidate.interests = json.dumps([i.dict() for i in profile.interests])
    if profile.awards is not None:
        candidate.awards = json.dumps([a.dict() for a in profile.awards])
    if profile.presentations is not None:
        candidate.presentations = json.dumps([p.dict() for p in profile.presentations])
    if profile.skill_categories is not None:
        candidate.skill_categories = json.dumps([sc.dict() for sc in profile.skill_categories])
    
    # Rest of the code...
```

## Template Generator Updates

The `latex_cv_generator.py` would need to be updated to use these new fields when generating CVs with either template:

1. For the FAANG template:
   - Use job_title in the OBJECTIVE section
   - Use skill_categories to populate the SKILLS table
   - Use projects with URLs in the PROJECTS section

2. For the Wenneker CV template:
   - Use photo in the sidebar
   - Use structured address in the sidebar
   - Use job_title as cvsubheading
   - Create Interests, Awards, and Communication Skills sections
   - Use skill_categories for the Software Development Skills section

## Implementation Plan

1. Update the database model and run a migration to add the new columns
2. Update the Pydantic schemas
3. Modify the endpoints to handle the new fields
4. Update the LaTeX template generator to use the new fields
5. Implement the enhanced UI in the frontend

This approach ensures backward compatibility while providing the additional fields needed for full template support.