from sqlalchemy.orm import Session
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
import openai
import os
import json
import logging
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_jobs(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Job).offset(skip).limit(limit).all()

def get_job(db: Session, job_id: int):
    return db.query(Job).filter(Job.id == job_id).first()

def create_job(db: Session, job: JobCreate):
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(db: Session, job_id: int, job: JobUpdate):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job:
        for key, value in job.dict(exclude_unset=True).items():
            setattr(db_job, key, value)
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job

def extract_job_details_with_ai(job_description: str) -> Dict[str, str]:
    """
    Extracts job title, company name, and location from a job description using OpenAI.
    
    Args:
        job_description: The full job listing text
        
    Returns:
        Dictionary with extracted job information including title, company, and location
    """
    # Default values in case of API failure
    default_result = {
        "title": "Job Position",
        "company": "Company",
        "location": "Not specified"
    }
    
    try:
        # Check if OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-api-key-here":
            logger.warning("OpenAI API key not set or is default value. Using default job details.")
            return default_result
        
        # Create the prompt for OpenAI
        prompt = f"""Extract the following information from this job listing:
1. Job Title/Position: The specific role or position being advertised
2. Company Name: The organization offering the position
3. Location: Where the job is located (city, country, or remote)

Note: This job listing may contain multiple positions, but I need you to identify THE MAIN JOB POSITION that this listing is primarily about. Do not list all positions if multiple are mentioned.

Return your answer as a JSON object with the following keys: "title", "company", and "location". 
- For the title, return ONLY the specific position title (e.g., "Software Engineer", not "Software Engineer at Google")
- For the company, return ONLY the company name
- If any information is not found, use "Not specified" as the value

Job Listing:
{job_description[:2000]}  # Limit to first 2000 chars for API efficiency

Return ONLY the JSON object, no other text:
"""

        # Call OpenAI API
        logger.info(f"Calling OpenAI API to extract job details from text ({len(job_description)} chars)")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a job details extraction assistant that extracts specific information from job listings. You ONLY return a valid JSON object with title, company, and location - nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            request_timeout=15
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {result_text[:100]}...")
        
        # Clean up the response to ensure it's valid JSON
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "", 1)
        if result_text.endswith("```"):
            result_text = result_text.replace("```", "", 1)
            
        # Parse the JSON response
        extracted_data = json.loads(result_text.strip())
        
        # Validate the response has expected keys
        for key in ["title", "company", "location"]:
            if key not in extracted_data or not extracted_data[key] or extracted_data[key] == "":
                extracted_data[key] = default_result[key]
                
        # Ensure values are strings
        for key in extracted_data:
            if not isinstance(extracted_data[key], str):
                extracted_data[key] = str(extracted_data[key])
        
        logger.info(f"Successfully extracted job details: {extracted_data}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error extracting job details with OpenAI: {e}")
        return default_result