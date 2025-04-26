"""
Script to set up sample data for testing
"""
import json
from app.database import SessionLocal, Base, engine
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.models.job import Job

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Create sample skills, experience, and education data
skills = ["Python", "JavaScript", "React", "FastAPI", "SQL", "Git", "AWS"]
experience = [
    {
        "position": "Backend Developer",
        "company": "TechCorp",
        "start_date": "2020-01",
        "end_date": "2022-12",
        "current": False,
        "description": "Developed scalable backend services using Python and FastAPI."
    },
    {
        "position": "Frontend Developer",
        "company": "WebSolutions",
        "start_date": "2018-06",
        "end_date": "",
        "current": True,
        "description": "Building responsive web applications with React and TypeScript."
    }
]
education = [
    {
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "institution": "Tech University",
        "start_date": "2014-09",
        "end_date": "2018-06",
        "current": False
    }
]

# Create a sample job
sample_job = {
    "title": "Full Stack Developer",
    "company": "Innovative Solutions",
    "location": "Remote",
    "description": """
    We are looking for a Full Stack Developer to join our team.
    
    Requirements:
    - 3+ years of experience with Python
    - Experience with React and modern JavaScript
    - Knowledge of SQL databases
    - Familiarity with cloud services (AWS, GCP)
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    - Participate in code reviews
    """
}

def setup_data():
    """Set up sample data in the database"""
    db = SessionLocal()
    try:
        # Create default user if it doesn't exist
        guest_user = db.query(User).filter(User.email == "guest@example.com").first()
        if not guest_user:
            guest_user = User(
                email="guest@example.com",
                name="Guest User",
                is_guest=True,
                is_active=True,
                locale="en"
            )
            db.add(guest_user)
            db.commit()
            db.refresh(guest_user)
            
        # Check if candidate already exists
        existing_candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == guest_user.id).first()
        if not existing_candidate:
            # Create candidate
            candidate = CandidateProfile(
                user_id=guest_user.id,
                name="John Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                location="New York, NY",
                is_default=True,
                summary="Experienced software developer with expertise in Python and web development.",
                skills=json.dumps(skills),
                experience=json.dumps(experience),
                education=json.dumps(education)
            )
            db.add(candidate)
            print("Sample candidate created")
        else:
            print("Candidate already exists, skipping")
        
        # Check if job already exists
        existing_job = db.query(Job).filter(Job.title == sample_job["title"]).first()
        if not existing_job:
            # Create job
            job = Job(
                title=sample_job["title"],
                company=sample_job["company"],
                location=sample_job["location"],
                description=sample_job["description"]
            )
            db.add(job)
            print("Sample job created")
        else:
            print("Job already exists, skipping")
        
        db.commit()
        print("Sample data setup completed successfully")
    
    except Exception as e:
        db.rollback()
        print(f"Error setting up sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    setup_data()