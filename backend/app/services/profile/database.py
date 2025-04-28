"""
Database operations for profile management.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.candidate import CandidateProfile
from app.models.user import User

logger = logging.getLogger(__name__)

async def get_user_profile(db: Session, user_id: int) -> Optional[CandidateProfile]:
    """
    Get a user's profile from the database
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        CandidateProfile if found, None otherwise
    """
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()

async def create_or_update_profile(db: Session, user_id: int, profile_data: Dict[str, Any]) -> CandidateProfile:
    """
    Create a new profile or update an existing one
    
    Args:
        db: Database session
        user_id: User ID
        profile_data: Profile data dictionary
        
    Returns:
        The updated or created CandidateProfile
    """
    # Check if profile exists
    existing_profile = await get_user_profile(db, user_id)
    
    # Convert JSON objects to strings
    profile_data_db = prepare_profile_for_db(profile_data)
    
    # Add user ID to profile data
    profile_data_db["user_id"] = user_id
    
    if existing_profile:
        logger.info(f"Updating existing profile for user {user_id}")
        
        # Update existing profile
        for key, value in profile_data_db.items():
            if hasattr(existing_profile, key):
                setattr(existing_profile, key, value)
        
        db_profile = existing_profile
    else:
        logger.info(f"Creating new profile for user {user_id}")
        
        # Create new profile with default is_default=True
        profile_data_db["is_default"] = True
        db_profile = CandidateProfile(**profile_data_db)
        db.add(db_profile)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

def prepare_profile_for_db(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare profile data for database insertion by converting complex objects to JSON strings
    
    Args:
        profile_data: Profile data dictionary with Python objects
        
    Returns:
        Dictionary with JSON strings for complex objects
    """
    # Copy the data to avoid modifying the original
    db_ready = {}
    
    # Handle basic fields
    simple_fields = ['name', 'email', 'phone', 'summary', 'location', 'linkedin', 
                    'website', 'job_title', 'photo']
    for field in simple_fields:
        if field in profile_data:
            db_ready[field] = profile_data[field]
    
    # Handle complex JSON fields
    json_fields = ['skills', 'experience', 'education', 'languages', 'certifications',
                  'projects', 'references', 'interests', 'awards', 'presentations', 
                  'skill_categories', 'creativity_levels']
    
    for field in json_fields:
        if field in profile_data and profile_data[field] is not None:
            # Convert dictionaries or lists to JSON strings
            if isinstance(profile_data[field], (list, dict)):
                db_ready[field] = json.dumps(profile_data[field])
    
    # Special handling for the address field (which is a nested object)
    if 'address' in profile_data and profile_data['address']:
        db_ready['address'] = json.dumps(profile_data['address'])
    
    return db_ready

def profile_to_dict(profile: CandidateProfile) -> Dict[str, Any]:
    """
    Convert a database profile model to a dictionary
    
    Args:
        profile: CandidateProfile database model
        
    Returns:
        Dictionary with profile data
    """
    # Ensure updated_at is always a valid datetime
    updated_at_value = getattr(profile, 'updated_at', None)
    if updated_at_value is None:
        updated_at_value = datetime.now()
    
    # Build the base dictionary with simple fields
    profile_dict = {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone or "",
        "summary": profile.summary or "",
        "location": getattr(profile, 'location', ""),
        "linkedin": getattr(profile, 'linkedin', ""),
        "website": getattr(profile, 'website', ""),
        "photo": getattr(profile, 'photo', None),
        "updated_at": updated_at_value
    }
    
    # Add job title if it exists
    if hasattr(profile, 'job_title'):
        profile_dict["job_title"] = profile.job_title
    
    # Parse JSON fields
    json_fields = [
        ('skills', []),
        ('experience', []),
        ('education', []),
        ('languages', []),
        ('certifications', []),
        ('projects', []),
        ('references', []),
        ('interests', []),
        ('awards', []),
        ('presentations', []),
        ('skill_categories', []),
        ('address', None)
    ]
    
    for field, default in json_fields:
        if hasattr(profile, field) and getattr(profile, field):
            try:
                profile_dict[field] = json.loads(getattr(profile, field))
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse JSON for field {field}")
                profile_dict[field] = default
        else:
            profile_dict[field] = default
    
    # Handle creativity levels separately since it's a special case
    if hasattr(profile, 'creativity_levels') and profile.creativity_levels:
        try:
            profile_dict['creativity_levels'] = json.loads(profile.creativity_levels)
        except (json.JSONDecodeError, TypeError):
            profile_dict['creativity_levels'] = None
    else:
        profile_dict['creativity_levels'] = None
    
    return profile_dict