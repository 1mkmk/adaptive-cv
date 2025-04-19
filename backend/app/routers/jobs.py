from fastapi import APIRouter, Depends, HTTPException, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import requests
from datetime import datetime
import logging
import traceback

# Fix the import to use the correct path
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobCreate
from app.services.job_scraper import extract_from_url
from app.services.job_service import extract_job_details_with_ai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    try:
        jobs = db.query(Job).all()
        return jobs
    except Exception as e:
        logger.error(f"Error in get_jobs: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/create", response_model=JobResponse)
def create_job(
    job_url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    requirements: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Handle URL-based job creation
    if job_url:
        try:
            # Extract job data using the job scraper
            logger.info(f"Extracting job from URL: {job_url}")
            job_data = extract_from_url(job_url)
            
            if not job_data:
                raise HTTPException(status_code=400, detail="Could not extract job information from the provided URL")
            
            # Format the complete description
            full_description = job_data.get("description", "")
            
            if "requirements" in job_data and job_data["requirements"]:
                req_text = job_data["requirements"]
                if isinstance(req_text, list):
                    req_text = "\n- " + "\n- ".join(req_text)
                full_description += f"\n\nRequirements:\n{req_text}"
                
            if "responsibilities" in job_data and job_data["responsibilities"]:
                resp_text = job_data["responsibilities"]
                if isinstance(resp_text, list):
                    resp_text = "\n- " + "\n- ".join(resp_text)
                full_description += f"\n\nResponsibilities:\n{resp_text}"
            
            # Create the job
            new_job = Job(
                title=job_data.get("title", "Job from URL"),
                company=job_data.get("company", "Company from URL"),
                location=job_data.get("location", "Remote"),
                description=full_description,
                source_url=job_url
            )
            
        except Exception as e:
            logger.error(f"Error processing job URL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process job URL: {str(e)}")
    
    # Handle manual job creation
    elif description:  # Only require description for manual entry
        full_description = description
        if requirements:
            full_description += "\n\nRequirements:\n" + requirements
        
        # Use OpenAI to extract more accurate job details if title or company is missing
        if not (title and company):
            logger.info("Using OpenAI to extract job details from description")
            extracted_info = extract_job_details_with_ai(full_description)
            
            # Only use extracted values if not provided manually
            title = title or extracted_info.get("title", "Job Position")
            company = company or extracted_info.get("company", "Company")
            location = location or extracted_info.get("location", "Not specified")
            
            logger.info(f"Extracted job details: Title: {title}, Company: {company}, Location: {location}")
            
        new_job = Job(
            title=title,
            company=company,
            location=location or "Not specified",
            description=full_description,
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid job information provided")
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/{job_id}", response_model=JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job: JobCreate, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in job.dict().items():
        setattr(db_job, key, value)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(db_job)
    db.commit()
    return {"detail": "Job deleted successfully"}