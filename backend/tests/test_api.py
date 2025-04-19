from fastapi.testclient import TestClient
from app.main import app
from app.database import create_database, recreate_database, engine, SessionLocal
from app.models.job import Job
from app.models.candidate import Candidate
from sqlalchemy.orm import Session
from app.database import get_db
import unittest
import json
from unittest.mock import patch, MagicMock

client = TestClient(app)

def setup_module(module):
    create_database()

def teardown_module(module):
    recreate_database()

def test_create_job():
    response = client.post(
        "/jobs/create", 
        data={
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "Remote",
            "description": "Develop and maintain software applications."
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Software Engineer"

def test_get_jobs():
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_job():
    # First create a job to update
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "Remote",
            "description": "Develop and maintain software applications."
        }
    )
    job_id = create_response.json()["id"]

    # Now update the job
    update_response = client.put(f"/jobs/{job_id}", json={
        "title": "Senior Software Engineer",
        "company": "Tech Company",
        "location": "Remote",
        "description": "Lead software development projects.",
        "source_url": "https://example.com/senior-job"
    })
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Senior Software Engineer"

def test_delete_job():
    # First create a job to delete
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "Remote",
            "description": "Develop and maintain software applications."
        }
    )
    job_id = create_response.json()["id"]

    # Now delete the job
    delete_response = client.delete(f"/jobs/{job_id}")
    assert delete_response.status_code == 200

    # Verify the job is deleted
    get_response = client.get(f"/jobs/{job_id}")
    assert get_response.status_code == 404

def create_test_profile(db: Session):
    """Helper function to create a test candidate profile"""
    # Check if a profile already exists
    candidate = db.query(Candidate).first()
    if candidate:
        return candidate
    
    # Create basic profile with JSON fields
    candidate = Candidate(
        name="Test User",
        email="test@example.com",
        phone="+1234567890",
        location="Test City",
        summary="Experienced software engineer with skills in Python and FastAPI.",
        skills=json.dumps(["Python", "FastAPI", "SQL", "Testing"]),
        experience=json.dumps([{
            "company": "Test Company",
            "position": "Software Engineer",
            "start_date": "2020-01",
            "end_date": "2023-01",
            "current": False,
            "description": "Developed and maintained web applications using Python."
        }]),
        education=json.dumps([{
            "institution": "Test University",
            "degree": "Bachelor's",
            "field": "Computer Science",
            "start_date": "2016-09",
            "end_date": "2020-05",
            "current": False
        }])
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate

@patch('app.services.cv_service.generate_fallback_cv')
def test_generate_cv_markdown(mock_fallback_cv):
    """Test that the CV generation endpoint works for markdown format"""
    # Configure mock to return a test CV
    mock_fallback_cv.return_value = "# Test CV\n\nThis is a test CV."
    
    # Create a job first
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "Python Developer",
            "company": "Tech Startup",
            "location": "Remote",
            "description": "We are looking for a Python developer with FastAPI experience."
        }
    )
    job_id = create_response.json()["id"]
    
    # Create a test profile using the database session
    with SessionLocal() as session:
        create_test_profile(session)
    
    # Now generate a CV
    response = client.post("/generate", json={
        "prompt": "We are looking for a Python developer with FastAPI experience.",
        "job_id": job_id,
        "format": "markdown"
    })
    
    assert response.status_code == 200
    assert "result" in response.json()
    assert response.json()["format"] == "markdown"

@patch('app.routers.generate.generate_cv_with_template')
def test_generate_cv_pdf(mock_generate_template):
    """Test that the PDF CV generation endpoint works"""
    # Create a mock PDF result
    mock_generate_template.return_value = {
        "pdf": "base64encodedpdfcontent", 
        "preview": "base64encodedpreviewimage"
    }
    
    # Create a job first
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "Senior Python Developer",
            "company": "Enterprise Corp",
            "location": "New York",
            "description": "Enterprise application development using Python and FastAPI."
        }
    )
    job_id = create_response.json()["id"]
    
    # Create a test profile using the database session
    with SessionLocal() as session:
        create_test_profile(session)
    
    # Generate a PDF CV
    response = client.get(f"/generate/pdf/{job_id}")
    
    assert response.status_code == 200
    assert "result" in response.json()
    assert response.json()["format"] == "pdf"
    assert "preview" in response.json()

@patch('app.services.latex_cv_generator.compile_latex_to_pdf')
@patch('app.services.latex_cv_generator.generate_latex_cv')
@patch('app.services.latex_cv_generator.prepare_latex_environment')
def test_cv_template_generation(mock_prepare_env, mock_generate_latex, mock_compile_latex):
    """Test the LaTeX CV generation process"""
    # Setup mocks
    mock_prepare_env.return_value = "/tmp/test_latex_dir"
    mock_generate_latex.return_value = "/tmp/test_latex_dir/output.tex"
    mock_compile_latex.return_value = ("/tmp/test_latex_dir/output.pdf", "/tmp/test_latex_dir/output_preview.png")
    
    # Create a job
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "LaTeX Expert",
            "company": "Document Systems Inc",
            "location": "Remote",
            "description": "Working with LaTeX and document generation systems."
        }
    )
    job_id = create_response.json()["id"]
    
    # Create a test profile using the database session
    with SessionLocal() as session:
        create_test_profile(session)
    
    # Create a mock for open and base64 encoding
    with patch("builtins.open", unittest.mock.mock_open(read_data=b"test pdf content")), \
         patch("base64.b64encode", return_value=b"base64encodedcontent"), \
         patch("base64.b64encode", return_value=b"base64encodedcontent"), \
         patch("os.path.exists", return_value=True):
        
        # Test the endpoint
        response = client.get(f"/generate/download/{job_id}")
        
        # Should return a streamed response, so status code 200 is what we test
        assert response.status_code == 200

# Integration test checking the whole CV generation flow
@unittest.skip("Skipping integration test that may require real LaTeX environment")
def test_cv_generation_integration():
    """Integration test for the entire CV generation process.
    Note: This test requires a real LaTeX environment and may take longer to run.
    """
    # Create a job
    create_response = client.post(
        "/jobs/create", 
        data={
            "title": "Integration Tester",
            "company": "Quality Assurance Ltd",
            "location": "Remote",
            "description": "Testing integrated systems with Python, FastAPI, and LaTeX."
        }
    )
    job_id = create_response.json()["id"]
    
    # Create a test profile using the database session
    with SessionLocal() as session:
        create_test_profile(session)
    
    # Generate a markdown CV first
    markdown_response = client.post("/generate", json={
        "prompt": "Testing integrated systems with Python, FastAPI, and LaTeX.",
        "job_id": job_id,
        "format": "markdown"
    })
    
    assert markdown_response.status_code == 200
    
    # Now generate a PDF version
    pdf_response = client.get(f"/generate/pdf/{job_id}")
    
    assert pdf_response.status_code == 200
    assert pdf_response.json()["format"] == "pdf"
    
    # Test direct download
    download_response = client.get(f"/generate/download/{job_id}")
    assert download_response.status_code == 200