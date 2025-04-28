"""
Router for profile management endpoints.
"""
import os
import logging
import base64
import tempfile
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.oauth import get_current_user
from ..models.user import User
from ..schemas.candidate import CandidateProfileSchema, CandidateResponse, CandidateUpdate, ProfileGenerationPrompt
from ..services.profile import (
    DocumentProcessor, 
    extract_profile_from_cv,
    get_user_profile,
    create_or_update_profile,
    profile_to_dict,
    ProfileAIGenerator
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to assets directory with CV samples
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../assets'))

# Initialize router
router = APIRouter(
    tags=["profile"]
)

# Initialize AI generator
ai_generator = ProfileAIGenerator()

@router.get("", response_model=CandidateResponse)
async def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the candidate profile for the current user"""
    profile = await get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile_to_dict(profile)

@router.get("/openai-status")
async def get_openai_status():
    """Check if OpenAI API key is configured"""
    return ProfileAIGenerator.check_openai_availability()

@router.post("/generate-from-prompt", response_model=CandidateResponse)
async def generate_profile_from_prompt(generation_data: ProfileGenerationPrompt, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Generate a profile based on a prompt and creativity levels"""
    try:
        logger.info(f"Generating profile from prompt: {generation_data.prompt[:100]}...")
        logger.info(f"Creativity levels: {generation_data.creativity_levels}")
        
        # Generate profile using AI
        profile_data = await ai_generator.generate_profile_from_prompt(
            prompt=generation_data.prompt,
            creativity_levels=generation_data.creativity_levels,
            job_description=generation_data.job_description
        )
        
        # Save to database
        db_profile = await create_or_update_profile(db, current_user.id, profile_data)
        
        return profile_to_dict(db_profile)
        
    except Exception as e:
        logger.error(f"Error generating profile from prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(e)}")

@router.post("", response_model=CandidateResponse)
async def create_profile(profile: CandidateProfileSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create or update the candidate profile for the current user"""
    # Convert Pydantic schema to dictionary
    profile_dict = profile.dict()
    
    # Handle nested objects correctly
    for key, value in profile_dict.items():
        if hasattr(value, 'dict') and callable(getattr(value, 'dict')):
            profile_dict[key] = value.dict()
        elif isinstance(value, list) and value and hasattr(value[0], 'dict') and callable(getattr(value[0], 'dict')):
            profile_dict[key] = [item.dict() for item in value]
    
    # Save to database
    db_profile = await create_or_update_profile(db, current_user.id, profile_dict)
    
    return profile_to_dict(db_profile)

@router.put("", response_model=CandidateResponse)
async def update_profile(profile: CandidateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update parts of the candidate profile for the current user"""
    # Get existing profile
    existing_profile = await get_user_profile(db, current_user.id)
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")
    
    # Convert Pydantic schema to dictionary, excluding unset fields
    profile_dict = profile.dict(exclude_unset=True)
    
    # Handle nested objects correctly
    for key, value in profile_dict.items():
        if hasattr(value, 'dict') and callable(getattr(value, 'dict')):
            profile_dict[key] = value.dict()
        elif isinstance(value, list) and value and hasattr(value[0], 'dict') and callable(getattr(value[0], 'dict')):
            profile_dict[key] = [item.dict() for item in value]
    
    # Update in database
    db_profile = await create_or_update_profile(db, current_user.id, profile_dict)
    
    return profile_to_dict(db_profile)

@router.post("/upload-photo", response_model=CandidateResponse)
async def upload_photo(photo_file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Upload a profile photo and save it as base64 encoded data"""
    logger.info(f"Uploading photo: {photo_file.filename}")
    
    # Check if photo is an image
    content_type = photo_file.content_type
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (limit to 2MB)
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    file_size = 0
    file_contents = b""
    
    # Read file in chunks to avoid memory issues
    while chunk := await photo_file.read(1024 * 1024):  # Read 1MB at a time
        file_contents += chunk
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 2MB")
    
    try:
        # Encode the image as base64
        image_base64 = base64.b64encode(file_contents).decode('utf-8')
        
        # Add data URI prefix for direct display in browser
        image_data_uri = f"data:{content_type};base64,{image_base64}"
        
        # Get existing profile for current user
        profile = await get_user_profile(db, current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")
        
        # Update only the photo field
        profile_update = {"photo": image_data_uri}
        db_profile = await create_or_update_profile(db, current_user.id, profile_update)
        
        logger.info(f"Successfully uploaded photo for profile ID: {profile.id}")
        return profile_to_dict(db_profile)
    
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

@router.post("/import-cv-test", response_model=CandidateResponse)
async def import_cv_test(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Test endpoint to import a profile from a sample CV in the assets directory.
    For development/testing purposes only.
    """
    try:
        import io
        
        sample_cv_path = os.path.join(ASSETS_DIR, "maciejkasik_cv.pdf")
        logger.info(f"Testing CV import with file: {sample_cv_path}")
        
        if not os.path.exists(sample_cv_path):
            raise HTTPException(status_code=404, detail=f"Sample CV not found at {sample_cv_path}")
        
        # Read the PDF file
        with open(sample_cv_path, "rb") as pdf_file:
            file_contents = pdf_file.read()
        
        # Extract text using our document processor
        cv_text, _ = await DocumentProcessor.extract_text_from_file(file_contents, "maciejkasik_cv.pdf")
        
        # Extract profile information
        extracted_profile = await extract_profile_from_cv(cv_text)
        
        # Save to database
        db_profile = await create_or_update_profile(db, current_user.id, extracted_profile)
        
        return profile_to_dict(db_profile)
    
    except Exception as e:
        logger.error(f"Error in test CV import: {e}")
        raise HTTPException(status_code=500, detail=f"Test CV import failed: {str(e)}")

@router.post("/import-cv", response_model=CandidateResponse)
async def import_cv_profile(cv_file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Import a profile from a CV document.
    Extracts information from the CV and creates or updates the profile.
    """
    try:
        logger.info(f"Importing CV: {cv_file.filename}")
        
        # Check file size (limit to 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        file_size = 0
        file_contents = b""
        
        # Read file in chunks to avoid memory issues
        while chunk := await cv_file.read(1024 * 1024):  # Read 1MB at a time
            file_contents += chunk
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
        
        # Extract text from the file
        try:
            cv_text, is_placeholder = await DocumentProcessor.extract_text_from_file(file_contents, cv_file.filename)
        except Exception as extract_error:
            logger.error(f"Error extracting text from CV: {extract_error}")
            raise HTTPException(status_code=400, detail=f"Could not extract text from file: {str(extract_error)}")
        
        # Extract profile from text
        try:
            extracted_profile = await extract_profile_from_cv(cv_text)
        except Exception as profile_error:
            logger.error(f"Error extracting profile data: {profile_error}")
            if is_placeholder:
                # If we already have a placeholder structure, try to parse it directly
                try:
                    import json
                    json_start = cv_text.find('{')
                    json_end = cv_text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = cv_text[json_start:json_end]
                        extracted_profile = json.loads(json_str)
                    else:
                        raise ValueError("Could not find valid JSON in placeholder")
                except Exception as placeholder_err:
                    logger.error(f"Error parsing placeholder CV: {placeholder_err}")
                    raise HTTPException(status_code=500, detail="Failed to extract profile data from CV")
            else:
                raise HTTPException(status_code=500, detail="Failed to extract profile data from CV")
        
        # Save to database
        db_profile = await create_or_update_profile(db, current_user.id, extracted_profile)
        
        return profile_to_dict(db_profile)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error importing CV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import CV: {str(e)}")