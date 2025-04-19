from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.candidate import Candidate
from app.schemas.job import JobCreate
from typing import List, Dict, Any
import os
import json
import openai
import logging
import re
from datetime import datetime
import base64

# Import our LaTeX CV generator
from app.services.latex_cv_generator import generate_cv_from_template

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_job(db: Session, job: JobCreate) -> Job:
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_jobs(db: Session, skip: int = 0, limit: int = 10) -> List[Job]:
    return db.query(Job).offset(skip).limit(limit).all()

def get_job(db: Session, job_id: int) -> Job:
    return db.query(Job).filter(Job.id == job_id).first()

def update_job(db: Session, job_id: int, job: JobCreate) -> Job:
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job:
        for key, value in job.dict().items():
            setattr(db_job, key, value)
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int) -> bool:
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
        return True
    return False

def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """Extract key requirements and skills from a job description using OpenAI."""
    try:
        prompt = f"""
        Analyze this job description with extreme thoroughness to extract EVERY SINGLE requirement that would be useful for creating a CV that passes ATS screening.
        
        Format the output as JSON with the following keys:
        - all_requirements: Comprehensive list of EVERY SINGLE requirement, qualification, and preference mentioned in the description
        - required_skills: List of all technical skills explicitly mentioned or implied in the job description
        - preferred_skills: List of skills that are mentioned as "nice to have" or "preferred" 
        - experience_level: Junior, Mid-level, Senior, etc.
        - experience_years: Required years of experience if specified (extract exact numbers and phrases)
        - education: Required education level with exact qualifications
        - key_responsibilities: Exhaustive list of every responsibility mentioned
        - industry_keywords: ALL domain-specific terminology and keywords from the description (important for ATS)
        - soft_skills: ALL soft skills like communication, leadership, teamwork, etc. mentioned
        - company_values: Any information about company culture or values mentioned
        - tools_and_technologies: EVERY specific tool, technology, platform, software, language mentioned
        - certifications: Any certifications or qualifications mentioned
        - exact_phrases: Extract 10-15 exact phrases from the job description that would be effective to include in a CV
        
        Job Description:
        {job_description}
        
        VERY IMPORTANT: Extract EVERY SINGLE requirement and keyword to ensure the CV will pass automated screening systems. Include EXACT PHRASING from the job description where possible.
        
        Return only the JSON output without any additional text or markdown formatting:
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert ATS (Applicant Tracking System) analyst who specializes in extracting EVERY SINGLE requirement and keyword from job descriptions. Your mission is to ensure that CVs include ALL requirements to pass automated screening systems. You meticulously identify and extract EVERY skill, qualification, responsibility, and keyword, using exact phrasing from the job description wherever possible. You are extremely thorough and never miss a single requirement."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up the result to get valid JSON
        if result.startswith("```json"):
            result = result.replace("```json", "", 1)
        if result.endswith("```"):
            result = result.replace("```", "", 1)
            
        return json.loads(result.strip())
    
    except Exception as e:
        logger.error(f"Error extracting job requirements: {e}")
        # Return a simplified fallback result
        return {
            "all_requirements": [],
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "Not specified",
            "experience_years": "Not specified",
            "education": "Not specified",
            "key_responsibilities": [],
            "industry_keywords": [],
            "soft_skills": [],
            "company_values": [],
            "tools_and_technologies": [],
            "certifications": [],
            "exact_phrases": []
        }

def get_candidate_profile(db: Session) -> Dict[str, Any]:
    """Retrieve the candidate profile from the database."""
    candidate = db.query(Candidate).first()
    if not candidate:
        return {}
    
    candidate_dict = candidate.__dict__
    
    # Parse JSON strings into Python objects
    for field in ['skills', 'experience', 'education', 'languages', 'certifications', 'projects']:
        if candidate_dict.get(field):
            try:
                if isinstance(candidate_dict[field], str):
                    candidate_dict[field] = json.loads(candidate_dict[field])
            except json.JSONDecodeError:
                candidate_dict[field] = []
    
    # Remove SQLAlchemy state
    if '_sa_instance_state' in candidate_dict:
        del candidate_dict['_sa_instance_state']
        
    return candidate_dict

def generate_cv(db: Session, job_description: str, job_id: int = None, format: str = "markdown") -> str:
    """
    Generate a tailored CV based on the candidate profile and job description.
    
    Args:
        db: Database session
        job_description: Job description text
        job_id: Optional job ID to save the CV to
        format: Output format ("markdown", "latex", "pdf")
        
    Returns:
        Generated CV content in the requested format
    """
    try:
        # If a specific format is requested, we'll use the appropriate generator
        if format.lower() == "pdf" and job_id is not None:
            try:
                logger.info(f"Generating PDF CV from LaTeX template for job ID: {job_id}")
                pdf_content = generate_cv_from_template(db, job_id)
                return pdf_content
            except Exception as latex_error:
                logger.error(f"Error generating LaTeX/PDF CV: {latex_error}")
                # Fallback to markdown if LaTeX generation fails
                logger.info("Falling back to markdown CV generation")
                
        # Jeśli OpenAI API nie jest dostępne, użyj wersji zastępczej
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-api-key-here":
            logger.warning("OpenAI API key not set. Using fallback CV generator.")
            return generate_fallback_cv(db, job_description)
            
        # Get candidate profile
        candidate_profile = get_candidate_profile(db)
        if not candidate_profile:
            return "Error: No candidate profile found. Please create a profile first."
        
        # Extract job requirements - próbujemy, ale jeśli nie działa, używamy podstawowej wersji
        try:
            job_requirements = extract_job_requirements(job_description)
        except Exception as req_error:
            logger.warning(f"Failed to extract job requirements: {req_error}. Using default values.")
            job_requirements = {
                "required_skills": [],
                "experience_level": "Not specified",
                "education": "Not specified",
                "key_responsibilities": []
            }
        
        # Format candidate profile data for the prompt
        skills = ", ".join(candidate_profile.get("skills", []))
        
        experience = ""
        for exp in candidate_profile.get("experience", []):
            exp_entry = f"- {exp.get('position')} at {exp.get('company')} "
            exp_entry += f"({exp.get('start_date', '')} to {exp.get('end_date', 'Present' if exp.get('current', False) else '')})\n"
            exp_entry += f"  {exp.get('description', '')}\n"
            experience += exp_entry
        
        education = ""
        for edu in candidate_profile.get("education", []):
            edu_entry = f"- {edu.get('degree')} in {edu.get('field')} from {edu.get('institution')} "
            edu_entry += f"({edu.get('start_date', '')} to {edu.get('end_date', 'Present' if edu.get('current', False) else '')})\n"
            education += edu_entry
        
        # Enhanced version of the prompt to ensure all job requirements are covered
        prompt = f"""Create a CV that ensures the candidate meets ALL requirements from the job posting.

        Profile:
        Name: {candidate_profile.get('name')}
        Email: {candidate_profile.get('email')}
        Phone: {candidate_profile.get('phone', '')}
        Summary: {candidate_profile.get('summary', '')[:200]}
        
        Skills: {skills[:300]}
        
        Experience:
        {experience[:500]}
        
        Education:
        {education[:300]}
        
        Job Description:
        {job_description[:800]}
        
        Instructions:
        1. Carefully analyze the job description to identify ALL key requirements, skills, and qualifications
        2. Ensure that EVERY requirement mentioned in the job posting is addressed in the CV
        3. For technical skills and qualifications mentioned in the posting, add them to the candidate's profile even if not explicitly listed in their original skills
        4. DO NOT embellish years of experience or specific time-related qualifications
        5. Embellish achievements and quantify them with plausible numbers (20-30% improvements, etc.)
        6. Add relevant-sounding projects or responsibilities that demonstrate the required skills
        7. Use plenty of industry-specific terminology from the job description
        8. Present the candidate's existing experience in a way that connects directly to the job requirements
        9. Structure the experience section to emphasize aspects that match the job requirements
        10. Format with Summary, Skills, Experience, Education sections
        11. Ensure the CV would pass automated screening systems by including ALL keywords from the job posting
        """
        
        try:
            # Ustawiamy timeout na 10 sekund
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional CV writer who specializes in creating resumes that ensure candidates meet ALL requirements in job postings. Your primary goal is to analyze job descriptions in detail and ensure that EVERY single requirement is covered in the CV. You add skills mentioned in the job posting to the candidate's profile, but you DO NOT embellish years of experience or time-specific qualifications. You restructure the candidate's existing experience to emphasize relevant aspects and add projects that demonstrate required skills. Your goal is to make the CV pass automated screening systems by including ALL keywords from the job posting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
                request_timeout=10
            )
            
            cv_content = response.choices[0].message.content.strip()
        except Exception as api_error:
            logger.error(f"OpenAI API error: {api_error}")
            return generate_fallback_cv(db, job_description)
        
        # Add footer
        cv_content += f"\n\n---\n*CV generated on {datetime.now().strftime('%Y-%m-%d')} by AdaptiveCV*"
        
        # Jeśli podano job_id, zapisz CV do tego job
        if job_id is not None:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                # Zapisz tylko jeśli nie generowaliśmy już PDF
                if format.lower() != "pdf":
                    job.cv = cv_content
                    db.commit()
                    logger.info(f"Saved markdown CV to job ID: {job_id}")
        
        return cv_content
    
    except Exception as e:
        logger.error(f"Error generating CV: {e}")
        return generate_fallback_cv(db, job_description)

def generate_fallback_cv(db: Session, job_description: str) -> str:
    """Generuje podstawową wersję CV bez użycia AI, gdy OpenAI API nie jest dostępne."""
    try:
        # Pobierz profil kandydata
        candidate_profile = get_candidate_profile(db)
        if not candidate_profile:
            return "Error: No candidate profile found. Please create a profile first."
        
        # Wyciągnij najważniejsze słowa kluczowe z opisu stanowiska
        keywords = extract_keywords_from_job(job_description)
        
        # Przygotuj dane profilu
        name = candidate_profile.get('name', 'Your Name')
        email = candidate_profile.get('email', 'your.email@example.com')
        phone = candidate_profile.get('phone', '')
        location = candidate_profile.get('location', '')
        linkedin = candidate_profile.get('linkedin', '')
        website = candidate_profile.get('website', '')
        summary = candidate_profile.get('summary', '')
        
        # Wybierz umiejętności pasujące do słów kluczowych
        skills = candidate_profile.get('skills', [])
        matched_skills = []
        other_skills = []
        
        for skill in skills:
            if any(keyword.lower() in skill.lower() for keyword in keywords):
                matched_skills.append(skill)
            else:
                other_skills.append(skill)
        
        # Przygotuj sekcje CV
        cv_header = f"""# CV: {name}

## Contact Information
- Email: {email}
- Phone: {phone}
- Location: {location}
"""
        if linkedin:
            cv_header += f"- LinkedIn: {linkedin}\n"
        if website:
            cv_header += f"- Website: {website}\n"

        cv_summary = f"""
## Professional Summary
{summary}
"""

        cv_skills = """
## Skills
"""
        if matched_skills:
            cv_skills += "### Key Skills\n"
            for skill in matched_skills:
                cv_skills += f"- {skill}\n"
        
        if other_skills:
            cv_skills += "\n### Additional Skills\n"
            for skill in other_skills[:10]:  # Ograniczamy do 10 dodatkowych umiejętności
                cv_skills += f"- {skill}\n"

        cv_experience = """
## Professional Experience
"""
        for exp in candidate_profile.get('experience', []):
            position = exp.get('position', '')
            company = exp.get('company', '')
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', 'Present') if exp.get('current', False) else exp.get('end_date', '')
            description = exp.get('description', '')
            
            cv_experience += f"### {position} | {company}\n"
            cv_experience += f"*{start_date} - {end_date}*\n\n"
            
            # Podświetl pasujące słowa kluczowe w opisie
            highlighted_description = description
            for keyword in keywords:
                if keyword.lower() in description.lower():
                    # Podświetl słowo kluczowe przez pogrubienie, ale tylko jeśli nie jest już wyróżnione
                    pattern = re.compile(f"(?<!\\**)\\b{re.escape(keyword)}\\b(?!\\**)", re.IGNORECASE)
                    highlighted_description = pattern.sub(f"**{keyword}**", highlighted_description)
            
            # Dodaj opis z podświetlonymi słowami kluczowymi
            cv_experience += f"{highlighted_description}\n\n"

        cv_education = """
## Education
"""
        for edu in candidate_profile.get('education', []):
            degree = edu.get('degree', '')
            field = edu.get('field', '')
            institution = edu.get('institution', '')
            start_date = edu.get('start_date', '')
            end_date = edu.get('end_date', 'Present') if edu.get('current', False) else edu.get('end_date', '')
            
            cv_education += f"### {degree} in {field} | {institution}\n"
            cv_education += f"*{start_date} - {end_date}*\n\n"

        # Złóż wszystko razem
        cv_content = cv_header + cv_summary + cv_skills + cv_experience + cv_education
        
        # Dodaj informację o dopasowaniu do stanowiska
        cv_content += f"""
## Job Match Analysis
This CV has been tailored for the following position:
```
{job_description[:200]}...
```

*Key matching keywords: {', '.join(keywords[:10])}*

---
*CV generated on {datetime.now().strftime('%Y-%m-%d')} by AdaptiveCV*
"""
        
        return cv_content
        
    except Exception as e:
        logger.error(f"Error generating fallback CV: {e}")
        return f"""# CV ERROR

Sorry, we couldn't generate your CV due to an error: {str(e)}

Please try again later or contact support.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')} by AdaptiveCV*
"""

def extract_keywords_from_job(job_description: str) -> list:
    """Wyciąga najważniejsze słowa kluczowe z opisu stanowiska."""
    # Lista popularnych słów kluczowych w różnych branżach
    common_keywords = [
        # Techniczne
        "Python", "JavaScript", "Java", "C++", "C#", "PHP", "Ruby", "Go", "Rust", "Swift", 
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", ".NET", "AWS", "Azure",
        "DevOps", "CI/CD", "Docker", "Kubernetes", "REST", "API", "GraphQL", "SQL", "NoSQL",
        "MongoDB", "PostgreSQL", "MySQL", "Oracle", "Git", "SVN", "Agile", "Scrum", "Kanban",
        
        # Biznesowe
        "Management", "Leadership", "Strategy", "Analysis", "Project", "Product", "Marketing", 
        "Sales", "Finance", "Accounting", "HR", "Customer", "Client", "Service", "Support",
        "Communication", "Presentation", "Negotiation", "Team", "Collaboration", "Problem-solving",
        
        # Umiejętności miękkie
        "Communication", "Teamwork", "Leadership", "Problem-solving", "Critical thinking",
        "Time management", "Adaptability", "Creativity", "Emotional intelligence", "Decision making"
    ]
    
    # Znajdź wszystkie słowa kluczowe, które występują w opisie stanowiska
    found_keywords = []
    for keyword in common_keywords:
        if keyword.lower() in job_description.lower():
            found_keywords.append(keyword)
    
    # Dodaj dodatkowe słowa kluczowe na podstawie częstych fraz w opisie
    # (W przyszłości można zaimplementować bardziej zaawansowane wyodrębnianie słów kluczowych)
    
    return found_keywords if found_keywords else ["experience", "skills", "knowledge", "education"]

def generate_cv_with_template(
    db: Session, 
    job_id: int, 
    template_id: str = None, 
    model: str = None, 
    custom_context: str = None
) -> Dict[str, str]:
    """
    Generate a CV using LaTeX template, based on the candidate profile and job details.
    
    Args:
        db: Database session
        job_id: ID of the job to generate CV for
        template_id: ID of the template to use (optional)
        model: Language model to use for generation (optional)
        custom_context: Additional context for CV generation (optional)
        
    Returns:
        Dictionary with PDF content and preview as Base64-encoded strings
        {
            "pdf": base64_encoded_pdf,
            "preview": base64_encoded_preview_image,
            "pdf_path": path_to_pdf_file,
            "latex_path": path_to_latex_file
        }
    """
    try:
        # Log additional parameters
        logger.info(f"Generating CV with template for job_id={job_id}, model={model}, custom_context={'provided' if custom_context else 'not provided'}")
        
        # Generate CV from template with additional parameters
        result = generate_cv_from_template(
            db, 
            job_id, 
            template_id, 
            model=model, 
            custom_context=custom_context
        )
        
        # Log warning if no preview was generated
        if not result.get("preview"):
            logger.warning(f"CV generated successfully, but failed to generate preview for job_id={job_id}")
            
        return result
    except Exception as e:
        logger.error(f"Error generating CV from template: {e}")
        # Fallback to markdown version
        job = get_job(db, job_id)
        if job:
            markdown_content = generate_cv(db, job.description, job_id, "markdown")
            # Zwracamy tylko tekst w formacie markdown bez podglądu
            return {
                "pdf": None,
                "markdown": markdown_content,
                "error": str(e)
            }
        else:
            return {
                "pdf": None,
                "markdown": "Error: Job not found",
                "error": "Job not found"
            }