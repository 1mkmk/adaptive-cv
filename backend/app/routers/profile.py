from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
import json
import os
import re
import tempfile
import base64
from datetime import datetime
import logging
import openai
import PyPDF2
import io


from ..database import get_db
from ..models.candidate import CandidateProfile
from ..auth.oauth import get_current_user
from ..models.user import User
from ..schemas.candidate import CandidateProfile as CandidateProfileSchema
from ..schemas.candidate import CandidateResponse, CandidateUpdate, ProfileGenerationPrompt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI - bezpośrednio z pliku .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
try:
    with open(env_path, 'r') as env_file:
        for line in env_file:
            if line.strip().startswith('OPENAI_API_KEY=') or line.strip().startswith('OPENAI_API_KEY='): 
                api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                openai.api_key = api_key
                logger.info(f"OpenAI API key loaded directly from .env file (length: {len(api_key)})")
                break
    if not openai.api_key:
        logger.warning("No OPENAI_API_KEY found in .env file. Using rule-based extraction only.")
except Exception as e:
    logger.error(f"Error reading .env file: {e}")
    logger.warning("Using rule-based extraction due to error reading OpenAI API key.")

router = APIRouter(
    tags=["profile"]
)

# Path to assets directory with CV samples
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../assets'))

async def extract_profile_from_cv(cv_text: str) -> dict:
    """
    Extract profile information from a CV using OpenAI.
    
    Args:
        cv_text: The text content of the CV
        
    Returns:
        Dictionary containing extracted profile information
    """
    try:
        # First let's log a small sample of the CV text for debugging
        preview_len = min(200, len(cv_text))
        logger.info(f"CV Text Preview (first {preview_len} chars): {cv_text[:preview_len]}")
        
        # Check if we have a valid OpenAI API key
        if openai.api_key and openai.api_key != "your-api-key-here":
            try:
                logger.info(f"Attempting OpenAI extraction with API key starting with {openai.api_key[:4]}...")
                
                # Prepare comprehensive prompt for information extraction of all fields
                prompt = f"""
                Extract the following information from this CV and format the response as JSON.
                The CV may be unstructured, so please extract as much information as possible.
                
                Basic information:
                1. name: Full name of the person
                2. email: Email address
                3. phone: Phone number
                4. summary: A brief professional summary (create one if not provided)
                5. location: City, State/Country (Extract Wrocław, Poland if present)
                6. linkedin: LinkedIn profile URL if available
                7. website: Personal website if available
                8. job_title: Current job title or profession
                
                Address information (if available, as an object):
                - line1: Street address
                - line2: Apartment/Suite number
                - city: City name
                - state: State/Province
                - postalCode: ZIP/Postal code
                - country: Country name
                
                Skills and experience:
                - skills: Array of skills mentioned
                - skill_categories: Array of skill categories with these properties:
                  * name: Category name (e.g., "Programming Languages", "Soft Skills")
                  * skills: Array of skills in this category
                
                - experience: Array of work experiences with these properties:
                  * company: Company name
                  * position: Job title
                  * start_date: Start date (YYYY-MM format)
                  * end_date: End date (YYYY-MM format, empty if current)
                  * current: Boolean, true if this is their current job
                  * description: Job description
                
                - education: Array of education entries with these properties:
                  * institution: School/University name
                  * degree: Degree type (Bachelor, Master, etc.)
                  * field: Field of study
                  * start_date: Start date (YYYY-MM format)
                  * end_date: End date (YYYY-MM format, empty if current)
                  * current: Boolean, true if currently studying here
                
                Additional sections (if mentioned):
                - projects: Array of projects with these properties:
                  * name: Project name
                  * description: Project description
                  * url: Project URL (if available)
                  * start_date: Start date (if available)
                  * end_date: End date (if available)
                
                - awards: Array of awards with these properties:
                  * title: Award title
                  * date: Date received
                  * issuer: Organization that gave the award
                  * description: Brief description of the award
                
                - presentations: Array of presentations with these properties:
                  * title: Presentation title
                  * date: Date of presentation
                  * venue: Where it was presented
                  * description: Brief description
                
                - interests: Array of interests with these properties:
                  * type: Either "professional" or "personal"
                  * description: Description of the interest
                
                CV text:
                {cv_text[:15000]}
                
                Return only valid JSON format with the extracted information. If you're unsure about a field, make a reasonable guess instead of leaving it empty. Assume a software development context when making inferences.
                """
                
                # Determine OpenAI API version by checking available attributes
                if hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                    logger.info("Using OpenAI API v1.0+ (Client)")
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo-16k",  # Use the 16k context version for handling longer CVs
                        messages=[
                            {"role": "system", "content": "You are a skilled assistant that extracts structured information from CVs. Be thorough and make reasonable inferences when information is unclear."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=4000  # Increased token limit for detailed extraction
                    )
                    
                    # Extract content from new API response structure
                    result = response.choices[0].message.content
                elif hasattr(openai, 'ChatCompletion'):
                    logger.info("Using OpenAI API v0.x (Legacy)")
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-16k",  # Use the 16k context version for more tokens
                        messages=[
                            {"role": "system", "content": "You are a skilled assistant that extracts structured information from CVs."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=4000
                    )
                    
                    # Extract content from old API response structure
                    result = response.choices[0].message.content.strip()
                else:
                    logger.error("Could not find appropriate OpenAI API version")
                    raise ImportError("OpenAI API not properly initialized")
                
                # Clean up JSON formatting
                if result.startswith("```json"):
                    result = result.replace("```json", "", 1)
                if result.endswith("```"):
                    result = result.replace("```", "", 1)
                    
                try:
                    # Parse the JSON result
                    extracted_data = json.loads(result.strip())
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse OpenAI response as JSON: {json_err}")
                    logger.info("Checking if the CV was our fallback structured format")
                    
                    # Check if we're working with our fallback JSON structure (for non-extractable PDFs)
                    if "This is a placeholder CV created because the original PDF could not be parsed" in cv_text:
                        logger.info("Detected placeholder CV, using direct parsing")
                        try:
                            # Try to extract just the JSON part from our structured text
                            json_part = cv_text.strip()
                            # Find the opening and closing braces
                            start_idx = json_part.find('{')
                            end_idx = json_part.rfind('}') + 1
                            if start_idx >= 0 and end_idx > start_idx:
                                json_str = json_part[start_idx:end_idx]
                                extracted_data = json.loads(json_str)
                                logger.info("Successfully parsed placeholder CV structure")
                            else:
                                raise ValueError("Could not find valid JSON in placeholder structure")
                        except Exception as placeholder_err:
                            logger.error(f"Failed to parse placeholder structure: {placeholder_err}")
                            # Create a minimum fallback data structure
                            extracted_data = {
                                "name": potential_name if 'potential_name' in locals() else (cv_file.filename.rsplit('.', 1)[0].replace('_', ' ') if 'cv_file' in locals() and cv_file.filename else "Unknown"),
                                "email": "youremail@example.com",
                                "phone": "+48 000 000 000",
                                "summary": "Placeholder profile created from PDF. Please edit all fields.",
                                "location": "Wrocław, Poland",
                                "skills": ["Technical Skills", "Professional Skills", "Software Development"],
                                "experience": [{
                                    "company": "Company Name",
                                    "position": "Position Title",
                                    "start_date": "2020-01",
                                    "end_date": "",
                                    "current": True,
                                    "description": "Please add job description here."
                                }],
                                "education": [{
                                    "institution": "University Name",
                                    "degree": "Degree",
                                    "field": "Field of Study",
                                    "start_date": "2015-09",
                                    "end_date": "2019-06",
                                    "current": False
                                }]
                            }
                    else:
                        # For other cases, re-raise the error
                        raise
                
                # Perform basic validation
                required_fields = ["name", "email", "skills", "experience", "education"]
                for field in required_fields:
                    if field not in extracted_data or not extracted_data[field]:
                        logger.warning(f"Missing required field in extraction: {field}")
                
                logger.info(f"Successfully extracted data using OpenAI with fields: {', '.join(extracted_data.keys())}")
                return extracted_data
                
            except Exception as openai_err:
                logger.error(f"Error using OpenAI: {openai_err}")
                logger.warning("Falling back to rule-based extraction")
        else:
            logger.warning("No valid OpenAI API key available, using rule-based extraction")
            
        # Attempt a basic rule-based extraction from CV text
        extracted_data = {}
        
        # Try to extract name (assuming it's one of the first all-caps or bold lines)
        lines = cv_text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            stripped = line.strip()
            # Simple heuristic: Names are usually short, have capital letters, and no special characters
            if stripped and len(stripped) < 40 and stripped.strip().split(' ')[0].istitle():
                if "CV" not in stripped and "resume" not in stripped.lower():
                    extracted_data["name"] = stripped
                    break
        
        # Try to extract email (look for @ sign)
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cv_text)
        if email_match:
            extracted_data["email"] = email_match.group(0)
            
        # Try to extract phone (look for patterns like +XX XXX XXX XXX)
        phone_match = re.search(r'(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{3,4}', cv_text)
        if phone_match:
            extracted_data["phone"] = phone_match.group(0)
            
        # Try to extract location
        location_matches = []
        cities = ["Wrocław", "Wroc law", "Wroclaw", "Warsaw", "Kraków", "Poznań", "Gdańsk", "Poland", "PL"]
        for city in cities:
            if city in cv_text:
                location_matches.append(city)
        
        if any(city in location_matches for city in ["Wrocław", "Wroc law", "Wroclaw"]):
            extracted_data["location"] = "Wrocław, Poland"
        elif "Warsaw" in location_matches:
            extracted_data["location"] = "Warsaw, Poland"
        elif "PL" in location_matches or "Poland" in location_matches:
            extracted_data["location"] = "Poland"
        
        # Find LinkedIn
        linkedin_match = re.search(r'linkedin\.com/[a-zA-Z0-9/-]+', cv_text)
        if linkedin_match:
            extracted_data["linkedin"] = linkedin_match.group(0)
            
        # Extract skills (using a common skill list)
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "Docker", 
            "Git", "AWS", "HTML", "CSS", "FastAPI", "Django", "Flask", "Express", 
            "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "GraphQL", "REST API",
            "MongoDB", "PostgreSQL", "MySQL", "Redis", "ElasticSearch", "Java", "C#",
            "C++", "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "Scala", "Haskell",
            "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn", "Kubernetes",
            "Terraform", "Ansible", "Jenkins", "CircleCI", "GitLab CI", "GitHub Actions",
            "Machine Learning", "Deep Learning", "Data Science", "Big Data", "Blockchain"
        ]
        
        skills = []
        for skill in common_skills:
            if skill in cv_text:
                skills.append(skill)
                
        # Dodatkowo szukamy języków programowania z małej litery
        lower_skills = ["python", "javascript", "typescript", "react", "node.js", "nextjs", "docker"]
        for skill in lower_skills:
            if skill in cv_text.lower() and skill.title() not in skills:
                skills.append(skill.title().replace(".js", ".js").replace("Nextjs", "Next.js"))
                
        extracted_data["skills"] = skills
        
        # Add dummy experience and education if not found (to satisfy requirement)
        extracted_data["experience"] = [
            {
                "company": "Company Found In CV",
                "position": "Position Extracted",
                "start_date": "2022-01",
                "end_date": "",
                "current": True,
                "description": "Role extracted from CV. Please review and edit for accuracy."
            }
        ]
        
        extracted_data["education"] = [
            {
                "institution": "University Found In CV",
                "degree": "Degree",
                "field": "Field",
                "start_date": "2015-09",
                "end_date": "2019-06",
                "current": False
            }
        ]
        
        # Add summary
        extracted_data["summary"] = "Profile imported from CV. Please review and edit details as needed."
        
        # Fill in defaults for anything missing - creating a complete profile structure
        # Extract name from filename if possible
        filename = "Unknown"
        potential_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('%20', ' ')
    
        if "name" not in extracted_data:
            extracted_data["name"] = potential_name or "John Doe"
        if "email" not in extracted_data:
            extracted_data["email"] = "youremail@example.com"
        if "phone" not in extracted_data:
            extracted_data["phone"] = "+48 000 000 000"
        if "location" not in extracted_data:
            extracted_data["location"] = "Wrocław, Poland"
        if "website" not in extracted_data:
            extracted_data["website"] = ""
        if "job_title" not in extracted_data:
            extracted_data["job_title"] = "Professional"
            
        # Add extended fields with defaults
        if "job_title" not in extracted_data:
            # Try to guess job title from CV text
            job_titles = ["Software Developer", "Software Engineer", "Data Scientist", 
                          "Project Manager", "Product Manager", "Designer"]
            for title in job_titles:
                if title.lower() in cv_text.lower():
                    extracted_data["job_title"] = title
                    break
            if "job_title" not in extracted_data:
                extracted_data["job_title"] = "Software Professional"
                
        # Add structured address
        if "address" not in extracted_data:
            # Try to extract city from location
            city = ""
            if "location" in extracted_data and extracted_data["location"]:
                city_match = re.search(r'([A-Za-z\s]+)', extracted_data["location"])
                if city_match:
                    city = city_match.group(1).strip()
            
            extracted_data["address"] = {
                "line1": "",
                "line2": "",
                "city": city or "Wrocław",
                "state": "",
                "postalCode": "",
                "country": "Poland"
            }
            
        # Add empty arrays for other extended fields
        if "projects" not in extracted_data:
            extracted_data["projects"] = [
                {
                    "name": "Portfolio Project",
                    "description": "Please add details of your project here.",
                    "url": "",
                    "start_date": "",
                    "end_date": ""
                }
            ]
            
        if "skill_categories" not in extracted_data:
            # Create basic categories from detected skills
            skill_categories = []
            if "skills" in extracted_data and extracted_data["skills"]:
                tech_skills = []
                lang_skills = []
                soft_skills = []
                
                programming_langs = ["Python", "Java", "JavaScript", "C++", "C#", "TypeScript"]
                languages = ["English", "Polish", "German", "French", "Spanish"]
                soft = ["Communication", "Teamwork", "Leadership", "Problem Solving"]
                
                for skill in extracted_data["skills"]:
                    if skill in programming_langs:
                        tech_skills.append(skill)
                    elif skill in languages:
                        lang_skills.append(skill)
                    elif skill in soft:
                        soft_skills.append(skill)
                    else:
                        tech_skills.append(skill)
                
                if tech_skills:
                    skill_categories.append({"name": "Technical Skills", "skills": tech_skills})
                if lang_skills:
                    skill_categories.append({"name": "Languages", "skills": lang_skills})
                if soft_skills:
                    skill_categories.append({"name": "Soft Skills", "skills": soft_skills})
                    
            extracted_data["skill_categories"] = skill_categories
            
        if "interests" not in extracted_data:
            extracted_data["interests"] = [
                {"type": "professional", "description": "Software Development, Technology"},
                {"type": "personal", "description": "Reading, Sports"}
            ]
            
        if "awards" not in extracted_data:
            extracted_data["awards"] = []
            
        if "presentations" not in extracted_data:
            extracted_data["presentations"] = []
            
        logger.info(f"Extracted data using rule-based approach with fields: {', '.join(extracted_data.keys())}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error extracting profile from CV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract profile: {str(e)}")

def db_profile_to_schema(db_profile: CandidateProfile) -> CandidateResponse:
    """Convert database profile model to Pydantic schema"""
    # Ensure updated_at is always a valid datetime
    updated_at_value = getattr(db_profile, 'updated_at', None)
    if updated_at_value is None:
        updated_at_value = datetime.now()
        
    return CandidateResponse(
        id=db_profile.id,
        name=db_profile.name,
        email=db_profile.email,
        phone=db_profile.phone or "",
        summary=db_profile.summary or "",
        location=getattr(db_profile, 'location', ""),
        linkedin=getattr(db_profile, 'linkedin', ""),
        website=getattr(db_profile, 'website', ""),
        photo=getattr(db_profile, 'photo', None),
        skills=json.loads(db_profile.skills) if db_profile.skills else [],
        experience=json.loads(db_profile.experience) if db_profile.experience else [],
        education=json.loads(db_profile.education) if db_profile.education else [],
        languages=json.loads(db_profile.languages) if hasattr(db_profile, 'languages') and db_profile.languages else [],
        certifications=json.loads(db_profile.certifications) if hasattr(db_profile, 'certifications') and db_profile.certifications else [],
        projects=json.loads(db_profile.projects) if hasattr(db_profile, 'projects') and db_profile.projects else [],
        references=json.loads(db_profile.references) if hasattr(db_profile, 'references') and db_profile.references else [],
        # Extended fields
        job_title=getattr(db_profile, 'job_title', None),
        address=json.loads(db_profile.address) if hasattr(db_profile, 'address') and db_profile.address else None,
        interests=json.loads(db_profile.interests) if hasattr(db_profile, 'interests') and db_profile.interests else [],
        awards=json.loads(db_profile.awards) if hasattr(db_profile, 'awards') and db_profile.awards else [],
        presentations=json.loads(db_profile.presentations) if hasattr(db_profile, 'presentations') and db_profile.presentations else [],
        skill_categories=json.loads(db_profile.skill_categories) if hasattr(db_profile, 'skill_categories') and db_profile.skill_categories else [],
        creativity_levels=json.loads(db_profile.creativity_levels) if hasattr(db_profile, 'creativity_levels') and db_profile.creativity_levels else None,
        updated_at=updated_at_value
    )

@router.get("", response_model=CandidateResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the candidate profile for the current user"""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile_to_schema(profile)

@router.get("/openai-status")
def get_openai_status():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    has_valid_key = api_key is not None and len(api_key) > 20  # podstawowa weryfikacja długości klucza
    
    return {
        "has_valid_key": has_valid_key,
        "key_status": "configured" if has_valid_key else "not_configured",
        "message": "Please set the OPENAI_API_KEY environment variable to use OpenAI features" if not has_valid_key else "OpenAI API key configured"
    }

@router.post("/generate-from-prompt", response_model=CandidateResponse)
async def generate_profile_from_prompt(generation_data: ProfileGenerationPrompt, db: Session = Depends(get_db)):
    """Generate a profile based on a prompt and creativity levels"""
    try:
        logger.info(f"Generating profile from prompt: {generation_data.prompt[:100]}...")
        logger.info(f"Creativity levels: {generation_data.creativity_levels}")
        
        # Check if we have a valid OpenAI API key
        if not openai.api_key or openai.api_key == "your-api-key-here":
            raise HTTPException(status_code=400, detail="OpenAI API key not configured. Please set your API key.")
        
        # Include creativity levels and job description in the prompt
        creativity_desc = "\n".join([f"- {section}: {level}/10 creativity level" for section, level in generation_data.creativity_levels.items()])
        
        job_desc_text = ""
        if generation_data.job_description:
            job_desc_text = f"\nPlease tailor the profile to this job description:\n{generation_data.job_description}"
        
        # Prepare comprehensive prompt for profile generation
        prompt = f"""
        Generate a complete CV profile based on this prompt:
        
        "{generation_data.prompt}"
        
        Use the following creativity levels for each section (0 means factual, 10 means very creative):
        {creativity_desc}
        {job_desc_text}
        
        Format your response as a JSON object matching this structure:
        {{
            "name": "Full Name",
            "email": "professional.email@example.com",
            "phone": "Phone number",
            "summary": "Professional summary...",
            "location": "City, Country",
            "linkedin": "LinkedIn profile URL",
            "website": "Personal website URL",
            "job_title": "Current job title",
            "address": {{
                "line1": "Street address",
                "line2": "Additional address info",
                "city": "City",
                "state": "State/Province",
                "postalCode": "Postal code",
                "country": "Country"
            }},
            "skills": ["Skill1", "Skill2", "Skill3"...],
            "skill_categories": [
                {{
                    "name": "Category name",
                    "skills": ["Skill1", "Skill2"...]
                }}
            ],
            "experience": [
                {{
                    "company": "Company name",
                    "position": "Job title",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM or empty if current",
                    "current": true/false,
                    "description": "Job description"
                }}
            ],
            "education": [
                {{
                    "institution": "University/School name",
                    "degree": "Degree type",
                    "field": "Field of study",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM",
                    "current": false
                }}
            ],
            "projects": [
                {{
                    "name": "Project name",
                    "description": "Project description",
                    "url": "Project URL",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM"
                }}
            ],
            "awards": [
                {{
                    "title": "Award title",
                    "date": "YYYY-MM",
                    "issuer": "Organization",
                    "description": "Description"
                }}
            ],
            "presentations": [
                {{
                    "title": "Title",
                    "date": "YYYY-MM",
                    "venue": "Conference/Venue",
                    "description": "Description"
                }}
            ],
            "interests": [
                {{
                    "type": "professional",
                    "description": "Professional interests"
                }},
                {{
                    "type": "personal",
                    "description": "Personal interests"
                }}
            ]
        }}
        
        Ensure all fields have appropriate content, and the JSON is properly formatted. For sections with high creativity levels, include more imaginative or diverse content while keeping it professionally plausible. For sections with low creativity levels, keep content straightforward and factual.
        """
        
        # Determine OpenAI API version
        try:
            if hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                logger.info("Using OpenAI API v1.0+ (Client)")
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer who creates complete, realistic CV profiles based on user prompts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                result = response.choices[0].message.content
            elif hasattr(openai, 'ChatCompletion'):
                logger.info("Using OpenAI API v0.x (Legacy)")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer who creates complete, realistic CV profiles based on user prompts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                result = response.choices[0].message.content
            else:
                raise ImportError("OpenAI API not properly initialized")
            
            # Clean up JSON formatting
            if result.startswith("```json"):
                result = result.replace("```json", "", 1)
            if result.endswith("```"):
                result = result.replace("```", "", 1)
                
            # Parse the JSON result
            try:
                profile_data = json.loads(result.strip())
                logger.info(f"Successfully generated profile with fields: {', '.join(profile_data.keys())}")
                
                # Ensure required fields are present
                required_fields = ["name", "email", "skills", "experience", "education"]
                for field in required_fields:
                    if field not in profile_data or not profile_data[field]:
                        profile_data[field] = [] if field in ["skills", "experience", "education"] else ""
                        logger.warning(f"Missing required field in generation: {field}")
                
                # Convert the JSON to CandidateProfile
                existing_profile = db.query(CandidateProfile).first()
                
                # Transform dict fields to their appropriate types
                if "experience" in profile_data:
                    for exp in profile_data["experience"]:
                        if "current" not in exp:
                            exp["current"] = False
                
                if "education" in profile_data:
                    for edu in profile_data["education"]:
                        if "current" not in edu:
                            edu["current"] = False
                
                # Create profile data object
                profile_data_clean = {
                    "name": profile_data.get("name", ""),
                    "email": profile_data.get("email", "user@example.com"),
                    "phone": profile_data.get("phone", ""),
                    "summary": profile_data.get("summary", ""),
                    "location": profile_data.get("location", ""),
                    "linkedin": profile_data.get("linkedin", ""),
                    "website": profile_data.get("website", ""),
                    "skills": json.dumps(profile_data.get("skills", [])),
                    "experience": json.dumps([exp for exp in profile_data.get("experience", [])]),
                    "education": json.dumps([edu for edu in profile_data.get("education", [])]),
                    
                    # Extended fields
                    "job_title": profile_data.get("job_title", ""),
                    "address": json.dumps(profile_data.get("address", {})) if profile_data.get("address") else None,
                    "interests": json.dumps(profile_data.get("interests", [])) if profile_data.get("interests") else None,
                    "awards": json.dumps(profile_data.get("awards", [])) if profile_data.get("awards") else None,
                    "presentations": json.dumps(profile_data.get("presentations", [])) if profile_data.get("presentations") else None,
                    "projects": json.dumps(profile_data.get("projects", [])) if profile_data.get("projects") else None,
                    "skill_categories": json.dumps(profile_data.get("skill_categories", [])) if profile_data.get("skill_categories") else None
                }
                
                if existing_profile:
                    # Update existing profile
                    for key, value in profile_data_clean.items():
                        setattr(existing_profile, key, value)
                    
                    db_profile = existing_profile
                else:
                    # Create new profile
                    db_profile = CandidateProfile(**profile_data_clean)
                    db.add(db_profile)
                
                db.commit()
                db.refresh(db_profile)
                
                return db_profile_to_schema(db_profile)
                
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse OpenAI response as JSON: {json_err}")
                logger.error(f"Response: {result}")
                raise HTTPException(status_code=500, detail="Failed to parse generated profile. Please try again.")
                
        except Exception as openai_err:
            logger.error(f"Error using OpenAI: {openai_err}")
            raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(openai_err)}")
            
    except Exception as e:
        logger.error(f"Error generating profile from prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(e)}")

@router.post("", response_model=CandidateResponse)
def create_profile(profile: CandidateProfileSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create or update the candidate profile for the current user"""
    existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    
    if existing_profile:
        # Update existing profile
        existing_profile.name = profile.name
        existing_profile.email = profile.email
        existing_profile.phone = profile.phone
        existing_profile.summary = profile.summary
        
        # Handle optional fields if they exist in the schema
        if hasattr(profile, 'location'):
            existing_profile.location = profile.location
        if hasattr(profile, 'linkedin'):
            existing_profile.linkedin = profile.linkedin
        if hasattr(profile, 'website'):
            existing_profile.website = profile.website
            
        # JSON fields
        existing_profile.skills = json.dumps([skill for skill in profile.skills])
        existing_profile.experience = json.dumps([exp.dict() for exp in profile.experience])
        existing_profile.education = json.dumps([edu.dict() for edu in profile.education])
        
        # Additional JSON fields from frontend
        if hasattr(profile, 'languages') and profile.languages:
            existing_profile.languages = json.dumps([lang.dict() for lang in profile.languages])
        if hasattr(profile, 'certifications') and profile.certifications:
            existing_profile.certifications = json.dumps([cert.dict() for cert in profile.certifications])
        if hasattr(profile, 'projects') and profile.projects:
            existing_profile.projects = json.dumps([proj.dict() for proj in profile.projects])
        if hasattr(profile, 'references') and profile.references:
            existing_profile.references = json.dumps([ref.dict() for ref in profile.references])
        
        # Extended fields
        if hasattr(profile, 'job_title'):
            existing_profile.job_title = profile.job_title
        if hasattr(profile, 'address') and profile.address:
            existing_profile.address = json.dumps(profile.address.dict())
        if hasattr(profile, 'interests') and profile.interests:
            existing_profile.interests = json.dumps([interest.dict() for interest in profile.interests])
        if hasattr(profile, 'awards') and profile.awards:
            existing_profile.awards = json.dumps([award.dict() for award in profile.awards])
        if hasattr(profile, 'presentations') and profile.presentations:
            existing_profile.presentations = json.dumps([presentation.dict() for presentation in profile.presentations])
        if hasattr(profile, 'skill_categories') and profile.skill_categories:
            existing_profile.skill_categories = json.dumps([category.dict() for category in profile.skill_categories])
        if hasattr(profile, 'creativity_levels') and profile.creativity_levels:
            existing_profile.creativity_levels = json.dumps(profile.creativity_levels)
            
        db_profile = existing_profile
    else:
        # Create new profile with all available fields
        profile_data = {
            "user_id": current_user.id,
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone or "",
            "summary": profile.summary or "",
            "skills": json.dumps([skill for skill in profile.skills]),
            "experience": json.dumps([exp.dict() for exp in profile.experience]),
            "education": json.dumps([edu.dict() for edu in profile.education]),
            "is_default": True
        }
        
        # Add optional fields if they exist in the schema
        if hasattr(profile, 'location'):
            profile_data["location"] = profile.location
        if hasattr(profile, 'linkedin'):
            profile_data["linkedin"] = profile.linkedin
        if hasattr(profile, 'website'):
            profile_data["website"] = profile.website
        if hasattr(profile, 'languages') and profile.languages:
            profile_data["languages"] = json.dumps([lang.dict() for lang in profile.languages])
        if hasattr(profile, 'certifications') and profile.certifications:
            profile_data["certifications"] = json.dumps([cert.dict() for cert in profile.certifications])
        if hasattr(profile, 'projects') and profile.projects:
            profile_data["projects"] = json.dumps([proj.dict() for proj in profile.projects])
        if hasattr(profile, 'references') and profile.references:
            profile_data["references"] = json.dumps([ref.dict() for ref in profile.references])
        
        # Extended fields
        if hasattr(profile, 'job_title'):
            profile_data["job_title"] = profile.job_title
        if hasattr(profile, 'address') and profile.address:
            profile_data["address"] = json.dumps(profile.address.dict())
        if hasattr(profile, 'interests') and profile.interests:
            profile_data["interests"] = json.dumps([interest.dict() for interest in profile.interests])
        if hasattr(profile, 'awards') and profile.awards:
            profile_data["awards"] = json.dumps([award.dict() for award in profile.awards])
        if hasattr(profile, 'presentations') and profile.presentations:
            profile_data["presentations"] = json.dumps([presentation.dict() for presentation in profile.presentations])
        if hasattr(profile, 'skill_categories') and profile.skill_categories:
            profile_data["skill_categories"] = json.dumps([category.dict() for category in profile.skill_categories])
        if hasattr(profile, 'creativity_levels') and profile.creativity_levels:
            profile_data["creativity_levels"] = json.dumps(profile.creativity_levels)
            
        db_profile = CandidateProfile(**profile_data)
        db.add(db_profile)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile_to_schema(db_profile)

@router.put("", response_model=CandidateResponse)
def update_profile(profile: CandidateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update parts of the candidate profile for the current user"""
    db_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")
    
    # Update only the fields that are provided
    if profile.name:
        db_profile.name = profile.name
    if profile.email:
        db_profile.email = profile.email
    if profile.phone:
        db_profile.phone = profile.phone
    if profile.summary:
        db_profile.summary = profile.summary
    
    # Additional fields from frontend
    if hasattr(profile, 'location') and profile.location:
        db_profile.location = profile.location
    if hasattr(profile, 'linkedin') and profile.linkedin:
        db_profile.linkedin = profile.linkedin
    if hasattr(profile, 'website') and profile.website:
        db_profile.website = profile.website
        
    # JSON fields
    if profile.skills:
        db_profile.skills = json.dumps([skill for skill in profile.skills])
    if profile.experience:
        db_profile.experience = json.dumps([exp.dict() for exp in profile.experience])
    if profile.education:
        db_profile.education = json.dumps([edu.dict() for edu in profile.education])
        
    # Additional JSON fields from frontend
    if hasattr(profile, 'languages') and profile.languages:
        db_profile.languages = json.dumps([lang.dict() for lang in profile.languages])
    if hasattr(profile, 'certifications') and profile.certifications:
        db_profile.certifications = json.dumps([cert.dict() for cert in profile.certifications])
    if hasattr(profile, 'projects') and profile.projects:
        db_profile.projects = json.dumps([proj.dict() for proj in profile.projects])
    if hasattr(profile, 'references') and profile.references:
        db_profile.references = json.dumps([ref.dict() for ref in profile.references])
    
    # Extended fields
    if hasattr(profile, 'job_title') and profile.job_title:
        db_profile.job_title = profile.job_title
    if hasattr(profile, 'address') and profile.address:
        db_profile.address = json.dumps(profile.address.dict())
    if hasattr(profile, 'interests') and profile.interests:
        db_profile.interests = json.dumps([interest.dict() for interest in profile.interests])
    if hasattr(profile, 'awards') and profile.awards:
        db_profile.awards = json.dumps([award.dict() for award in profile.awards])
    if hasattr(profile, 'presentations') and profile.presentations:
        db_profile.presentations = json.dumps([presentation.dict() for presentation in profile.presentations])
    if hasattr(profile, 'skill_categories') and profile.skill_categories:
        db_profile.skill_categories = json.dumps([category.dict() for category in profile.skill_categories])
    if hasattr(profile, 'creativity_levels') and profile.creativity_levels:
        db_profile.creativity_levels = json.dumps(profile.creativity_levels)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile_to_schema(db_profile)

@router.post("/upload-photo", response_model=CandidateResponse)
async def upload_photo(photo_file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Upload a profile photo and save it as base64 encoded data.
    """
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
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")
        
        # Update photo field
        profile.photo = image_data_uri
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Successfully uploaded photo for profile ID: {profile.id}")
        return db_profile_to_schema(profile)
    
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

@router.post("/import-cv-test", response_model=CandidateResponse)
async def import_cv_test(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Test endpoint to import a profile from a sample CV in the assets directory.
    For development/testing purposes only.
    """
    sample_cv_path = os.path.join(ASSETS_DIR, "maciejkasik_cv.pdf")
    logger.info(f"Testing CV import with file: {sample_cv_path}")
    
    if not os.path.exists(sample_cv_path):
        raise HTTPException(status_code=404, detail=f"Sample CV not found at {sample_cv_path}")
    
    try:
        # Read the PDF file
        with open(sample_cv_path, "rb") as pdf_file:
            file_contents = pdf_file.read()
        
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_contents))
        cv_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            cv_text += page.extract_text() + "\n"
        
        # Log some of the text for debugging
        logger.info(f"Extracted {len(cv_text)} characters from PDF. First 200 chars: {cv_text[:200]}")
        
        # Extract profile information
        extracted_profile = await extract_profile_from_cv(cv_text)
        
        # Process extracted information
        profile_data = {
            "user_id": current_user.id,
            "name": extracted_profile.get("name", ""),
            "email": extracted_profile.get("email", ""),
            "phone": extracted_profile.get("phone", ""),
            "summary": extracted_profile.get("summary", ""),
            "location": extracted_profile.get("location", ""),
            "linkedin": extracted_profile.get("linkedin", ""),
            "website": extracted_profile.get("website", ""),
            "skills": json.dumps(extracted_profile.get("skills", [])),
            "experience": json.dumps(extracted_profile.get("experience", [])),
            "education": json.dumps(extracted_profile.get("education", [])),
            "is_default": True
        }
        
        # Update or create profile
        existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        
        if existing_profile:
            for key, value in profile_data.items():
                if key != "user_id":  # Don't update user_id
                    setattr(existing_profile, key, value)
            db_profile = existing_profile
        else:
            db_profile = CandidateProfile(**profile_data)
            db.add(db_profile)
        
        db.commit()
        db.refresh(db_profile)
        
        return db_profile_to_schema(db_profile)
    
    except Exception as e:
        logger.error(f"Error in test CV import: {e}")
        raise HTTPException(status_code=500, detail=f"Test CV import failed: {str(e)}")

@router.post("/import-cv", response_model=CandidateResponse)
async def import_cv_profile(cv_file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Import a profile from a CV document.
    Extracts information from the CV and creates or updates the profile.
    
    This function is designed to never fail completely - it will always return some kind of profile,
    even if the CV cannot be parsed. The worst case scenario is that it will return a placeholder
    profile that the user can then edit manually.
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
    
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(cv_file.filename)[1]) as temp_file:
            temp_file.write(file_contents)
            temp_file_path = temp_file.name
        
        # Extract text based on file type
        cv_text = ""
        file_ext = os.path.splitext(cv_file.filename.lower())[1] if cv_file.filename else ""
        
        if file_ext == '.pdf':
            # Parse PDF file
            try:
                logger.info("Parsing PDF file using PyPDF2")
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_contents))
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    cv_text += page.extract_text() + "\n"
                
                # If PyPDF2 fails to extract text, try PyMuPDF (fitz)
                if not cv_text or cv_text.strip() == "":
                    logger.info("PyPDF2 extraction returned empty result. Trying PyMuPDF...")
                    try:
                        import fitz  # PyMuPDF
                        
                        # Save to temporary file for PyMuPDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                            temp_pdf.write(file_contents)
                            temp_pdf_path = temp_pdf.name
                        
                        # Open the PDF with PyMuPDF
                        doc = fitz.open(temp_pdf_path)
                        pymupdf_text = ""
                        
                        # Extract text from each page
                        for page_num in range(len(doc)):
                            page = doc[page_num]
                            pymupdf_text += page.get_text() + "\n"
                        
                        # Clean up temp file
                        os.unlink(temp_pdf_path)
                        
                        if pymupdf_text.strip():
                            logger.info(f"Successfully extracted {len(pymupdf_text)} characters using PyMuPDF")
                            cv_text = pymupdf_text
                        else:
                            logger.warning("PyMuPDF extraction returned empty result")
                    
                    except Exception as pymupdf_err:
                        logger.warning(f"PyMuPDF extraction failed: {pymupdf_err}")
                
                # If we still couldn't extract any text, try OCR as fallback
                if not cv_text or cv_text.strip() == "":
                    logger.info("PDF text extraction returned empty result. Attempting OCR fallback...")
                    try:
                        # Save PDF to a temporary file for OCR processing
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                            temp_pdf.write(file_contents)
                            temp_pdf_path = temp_pdf.name
                        
                        # Try to use OCR with pytesseract if available
                        try:
                            import pytesseract
                            from pdf2image import convert_from_path
                            
                            logger.info(f"Using pytesseract OCR on PDF: {temp_pdf_path}")
                            # Convert PDF to images
                            images = convert_from_path(temp_pdf_path)
                            
                            # Extract text from each image using OCR
                            ocr_text = ""
                            for i, image in enumerate(images):
                                logger.info(f"Processing page {i+1} with OCR")
                                page_text = pytesseract.image_to_string(image)
                                ocr_text += page_text + "\n"
                                # Print actual OCR results to log for debugging
                                logger.info(f"OCR text from page {i+1} (first 200 chars): {page_text[:200]}")
                            
                            if ocr_text.strip():
                                logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR")
                                logger.info(f"OCR result (first 400 chars): {ocr_text[:400]}")
                                cv_text = ocr_text
                            else:
                                logger.warning("OCR extraction returned empty result")
                        except ImportError:
                            logger.warning("pytesseract or pdf2image not installed, installing automatically...")
                            try:
                                import subprocess
                                # Attempt to install missing packages
                                logger.info("Trying to install pytesseract and pdf2image...")
                                subprocess.run(['pip', 'install', 'pytesseract', 'pdf2image'], check=True)
                                
                                # Retry OCR after installation
                                import importlib
                                import sys
                                importlib.invalidate_caches()
                                
                                # Try to import again
                                try:
                                    if 'pytesseract' in sys.modules:
                                        del sys.modules['pytesseract']
                                    if 'pdf2image' in sys.modules:
                                        del sys.modules['pdf2image']
                                        
                                    import pytesseract
                                    from pdf2image import convert_from_path
                                    
                                    # Configure custom Tesseract path if available
                                    custom_path = os.environ.get('TESSERACT_PATH')
                                    if custom_path and os.path.exists(custom_path):
                                        logger.info(f"Using custom Tesseract path: {custom_path}")
                                        pytesseract.pytesseract.tesseract_cmd = custom_path
                                    # Try a few common paths
                                    elif os.path.exists('/usr/local/bin/tesseract'):
                                        logger.info("Using Tesseract at /usr/local/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
                                    elif os.path.exists('/usr/bin/tesseract'):
                                        logger.info("Using Tesseract at /usr/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
                                    elif os.path.exists('/opt/homebrew/bin/tesseract'):
                                        logger.info("Using Tesseract at /opt/homebrew/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
                                        
                                    logger.info(f"Successfully installed packages. Retrying OCR on PDF: {temp_pdf_path}")
                                    # Convert PDF to images
                                    images = convert_from_path(temp_pdf_path)
                                    
                                    # Extract text from each image using OCR
                                    ocr_text = ""
                                    for i, image in enumerate(images):
                                        logger.info(f"Processing page {i+1} with OCR after installation")
                                        page_text = pytesseract.image_to_string(image)
                                        ocr_text += page_text + "\n"
                                        # Print actual OCR results to log for debugging
                                        logger.info(f"OCR text from page {i+1} (first 200 chars): {page_text[:200]}")
                                    
                                    if ocr_text.strip():
                                        logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR after installation")
                                        logger.info(f"OCR result (first 400 chars): {ocr_text[:400]}")
                                        cv_text = ocr_text
                                    else:
                                        logger.warning("OCR extraction returned empty result even after installation")
                                except Exception as retry_error:
                                    logger.error(f"OCR retry failed after installation: {retry_error}")
                                    
                            except Exception as install_error:
                                logger.error(f"Failed to install packages: {install_error}")
                            
                            # Alternative: Try to call system 'pdftotext' command as fallback
                            try:
                                import subprocess
                                logger.info("Attempting OCR with pdftotext system command")
                                txt_output = tempfile.NamedTemporaryFile(delete=False, suffix='.txt').name
                                subprocess.run(['pdftotext', temp_pdf_path, txt_output], check=True)
                                
                                with open(txt_output, 'r', encoding='utf-8', errors='ignore') as f:
                                    cv_text = f.read()
                                
                                if cv_text.strip():
                                    logger.info(f"Successfully extracted {len(cv_text)} characters using pdftotext")
                                else:
                                    logger.warning("pdftotext extraction returned empty result")
                                    
                                # Clean up temp file
                                os.unlink(txt_output)
                            except Exception as alt_ocr_error:
                                logger.error(f"Alternative OCR method failed: {alt_ocr_error}")
                        
                        # Clean up temp PDF file
                        os.unlink(temp_pdf_path)
                        
                    except Exception as ocr_error:
                        logger.error(f"OCR processing error: {ocr_error}")
                
                # If all extraction methods failed, try a last-resort approach with OpenAI vision
                if not cv_text or cv_text.strip() == "":
                    logger.info("Text extraction failed. Attempting to treat PDF as images for analysis...")
                    
                    try:
                        import fitz  # PyMuPDF for image extraction
                        import cv2
                        import numpy as np
                        from PIL import Image
                        
                        # Save PDF to temp file for processing
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                            temp_pdf.write(file_contents)
                            temp_pdf_path = temp_pdf.name
                        
                        # Open the PDF
                        doc = fitz.open(temp_pdf_path)
                        image_descriptions = []
                        
                        # Process each page as an image
                        for page_num in range(len(doc)):
                            logger.info(f"Processing PDF page {page_num+1} as image")
                            page = doc[page_num]
                            
                            # Render page to an image (PNG)
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                            img_path = f"{temp_pdf_path}_page_{page_num}.png"
                            pix.save(img_path)
                            
                            # Create a raw description of what's in the image using OpenCV
                            img = cv2.imread(img_path)
                            if img is not None:
                                # Simple image analysis to detect text-like content
                                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                
                                # Check if the image has enough contours that could be text
                                if len(contours) > 50:  # Arbitrary threshold for text-like content
                                    logger.info(f"Image analysis: Found {len(contours)} potential text elements on page {page_num+1}")
                                    
                                    # We'll use this page for manual description
                                    image_descriptions.append(f"PDF Page {page_num+1} appears to contain text-based content but could not be extracted automatically.")
                            
                            # Store image paths for later processing
                            logger.info(f"Image saved temporarily at: {img_path}")
                            # Don't unlink immediately, we might need these for OCR later
                            # We'll clean them up at the end of the function
                        
                        # Clean up the temp PDF
                        os.unlink(temp_pdf_path)
                        
                        if image_descriptions:
                            # Create a synthetic CV text that explains what's in the PDF
                            cv_text = "CV CONTENT ANALYSIS (EXTRACTED FROM IMAGES):\n\n"
                            cv_text += "\n".join(image_descriptions)
                            cv_text += "\n\nNote: This CV appears to be a scanned document or protected PDF. Only limited information could be extracted."
                            
                            logger.info(f"Created synthetic description of PDF content with {len(cv_text)} characters")
                            logger.info(f"Synthetic content: {cv_text}")
                            
                            # If we have access to tesseract, try direct OCR on the images as a last resort
                            try:
                                import pytesseract
                                from PIL import Image
                                # os is already imported at the top level
                                
                                # Check if Tesseract is properly installed on the system
                                try:
                                    tesseract_version = pytesseract.get_tesseract_version()
                                    logger.info(f"Tesseract version: {tesseract_version}")
                                except Exception as tesseract_err:
                                    logger.warning(f"Tesseract not properly installed on system: {tesseract_err}")
                                    logger.warning("To install Tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
                                    
                                    # Configure custom Tesseract path if the user specified it in environment
                                    custom_path = os.environ.get('TESSERACT_PATH')
                                    if custom_path and os.path.exists(custom_path):
                                        logger.info(f"Using custom Tesseract path: {custom_path}")
                                        pytesseract.pytesseract.tesseract_cmd = custom_path
                                    # Try a few common paths
                                    elif os.path.exists('/usr/local/bin/tesseract'):
                                        logger.info("Using Tesseract at /usr/local/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
                                    elif os.path.exists('/usr/bin/tesseract'):
                                        logger.info("Using Tesseract at /usr/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
                                    elif os.path.exists('/opt/homebrew/bin/tesseract'):
                                        logger.info("Using Tesseract at /opt/homebrew/bin/tesseract")
                                        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
                                    else:
                                        # Continue without raising error, we'll skip Tesseract and use other methods
                                        logger.warning("Skipping Tesseract OCR and trying other methods")
                                
                                logger.info("Attempting direct OCR on saved images as final attempt...")
                                # Get list of all temporary image files created earlier
                                img_files = [f for f in os.listdir(os.path.dirname(temp_pdf_path)) 
                                           if f.startswith(os.path.basename(temp_pdf_path)) and f.endswith('.png')]
                                
                                if img_files:
                                    direct_ocr_text = ""
                                    for img_file in img_files:
                                        img_path = os.path.join(os.path.dirname(temp_pdf_path), img_file)
                                        if os.path.exists(img_path):
                                            logger.info(f"Running direct OCR on image: {img_path}")
                                            try:
                                                img = Image.open(img_path)
                                                page_text = pytesseract.image_to_string(img)
                                                direct_ocr_text += page_text + "\n"
                                                logger.info(f"Direct OCR result (first 200 chars): {page_text[:200]}")
                                            except Exception as img_ocr_err:
                                                logger.error(f"Error during direct OCR on image: {img_ocr_err}")
                                    
                                    if direct_ocr_text.strip():
                                        logger.info(f"Successfully extracted {len(direct_ocr_text)} characters using direct OCR")
                                        # Replace the synthetic text with actual OCR text
                                        cv_text = direct_ocr_text
                                    else:
                                        logger.warning("Direct OCR extraction returned empty result")
                            except ImportError:
                                logger.warning("pytesseract not available for direct OCR")
                            except Exception as final_ocr_err:
                                logger.error(f"Final OCR attempt failed: {final_ocr_err}")
                        else:
                            logger.error("No usable content could be detected in the PDF images")
                    except Exception as img_err:
                        logger.error(f"Image-based PDF analysis failed: {img_err}")
                
                # Final check if we still don't have text - provide a minimal CV structure for OpenAI to work with
                if not cv_text or cv_text.strip() == "":
                    logger.warning("All extraction methods failed. Creating minimal CV structure for further processing")
                    
                    # Before giving up completely, try one more direct approach with a different extractor
                    try:
                        logger.info("Attempting one final extraction with tika-python as last resort...")
                        # Try to import tika
                        try:
                            from tika import parser
                            
                            # Save to temporary file for tika
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                                temp_pdf.write(file_contents)
                                temp_pdf_path = temp_pdf.name
                            
                            # Parse PDF with tika
                            parsed = parser.from_file(temp_pdf_path)
                            tika_text = parsed["content"]
                            
                            # Clean up temp file
                            os.unlink(temp_pdf_path)
                            
                            if tika_text and tika_text.strip():
                                logger.info(f"Successfully extracted {len(tika_text)} characters using tika")
                                logger.info(f"Tika extraction result (first 200 chars): {tika_text[:200]}")
                                cv_text = tika_text
                        except ImportError:
                            logger.warning("tika-python not installed, attempting to install...")
                            try:
                                import subprocess
                                subprocess.run(['pip', 'install', 'tika'], check=True)
                                
                                # Retry after installation
                                import importlib
                                import sys
                                importlib.invalidate_caches()
                                
                                if 'tika' in sys.modules:
                                    del sys.modules['tika']
                                    
                                from tika import parser
                                
                                # Save to temporary file for tika
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                                    temp_pdf.write(file_contents)
                                    temp_pdf_path = temp_pdf.name
                                
                                # Initialize tika
                                parser.from_buffer("test")  # Init the JVM
                                
                                # Parse PDF with tika
                                parsed = parser.from_file(temp_pdf_path)
                                tika_text = parsed["content"]
                                
                                # Clean up temp file
                                os.unlink(temp_pdf_path)
                                
                                if tika_text and tika_text.strip():
                                    logger.info(f"Successfully extracted {len(tika_text)} characters using tika after installation")
                                    logger.info(f"Tika extraction result (first 200 chars): {tika_text[:200]}")
                                    cv_text = tika_text
                                else:
                                    logger.warning("Tika extraction returned empty result")
                            except Exception as tika_install_error:
                                logger.error(f"Failed to install or use tika: {tika_install_error}")
                    except Exception as final_extraction_error:
                        logger.error(f"Final extraction attempt failed: {final_extraction_error}")
                    
                    # If all else fails, use filename as potential name
                    filename = cv_file.filename or "Unknown"
                    # Remove extension and underscores
                    potential_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('%20', ' ')
                    
                    # Create a structured JSON-like text that OpenAI can parse more easily
                    cv_text = f"""
                    {{
                        "name": "{potential_name}",
                        "email": "youremail@example.com",
                        "phone": "+48 000 000 000",
                        "summary": "Experienced professional with expertise in relevant fields. NOTE: This is a placeholder CV created because the original PDF could not be parsed. Please edit all fields with your actual information.",
                        "location": "Wrocław, Poland",
                        "linkedin": "linkedin.com/in/yourprofile",
                        "job_title": "Software Professional",
                        "skills": ["Technical Skills", "Communication", "Problem Solving"],
                        "experience": [
                            {{
                                "company": "Current Company",
                                "position": "Current Position",
                                "start_date": "2020-01",
                                "end_date": "",
                                "current": true,
                                "description": "Please add your current job responsibilities here."
                            }},
                            {{
                                "company": "Previous Company",
                                "position": "Previous Position",
                                "start_date": "2018-01",
                                "end_date": "2019-12",
                                "current": false,
                                "description": "Please add your previous job responsibilities here."
                            }}
                        ],
                        "education": [
                            {{
                                "institution": "University Name",
                                "degree": "Degree Title",
                                "field": "Field of Study",
                                "start_date": "2014-09",
                                "end_date": "2018-06",
                                "current": false
                            }}
                        ]
                    }}
                    """
                    
                    logger.info(f"Created minimal CV text structure with {len(cv_text)} characters")
                    
            except Exception as pdf_error:
                logger.error(f"Error parsing PDF: {pdf_error}")
                raise HTTPException(status_code=400, detail=f"Could not read PDF file: {str(pdf_error)}")
        elif file_ext in ['.doc', '.docx']:
            # For Word docs, we'd use a library like python-docx here
            # For now, just inform the user we don't support these formats yet
            raise HTTPException(status_code=400, detail="Word document parsing not yet supported. Please convert to PDF or plain text.")
        else:
            # Assume it's a text file
            logger.info("Parsing as text file")
            cv_text = file_contents.decode('utf-8', errors='ignore')
        
        # If we couldn't extract any text, return an error
        if not cv_text or cv_text.strip() == "":
            raise HTTPException(status_code=400, detail="Could not extract text from the provided file. Please try a different format.")
            
        logger.info(f"Extracted {len(cv_text)} characters of text from CV")
        
        # Extract profile information from CV
        extracted_profile = await extract_profile_from_cv(cv_text)
        
        # Process the extracted information to match our database schema
        profile_data = {
            # Basic fields
            "user_id": current_user.id,
            "name": extracted_profile.get("name", ""),
            "email": extracted_profile.get("email", ""),
            "phone": extracted_profile.get("phone", ""),
            "summary": extracted_profile.get("summary", ""),
            "location": extracted_profile.get("location", ""),
            "linkedin": extracted_profile.get("linkedin", ""),
            "website": extracted_profile.get("website", ""),
            "skills": json.dumps(extracted_profile.get("skills", [])),
            "experience": json.dumps(extracted_profile.get("experience", [])),
            "education": json.dumps(extracted_profile.get("education", [])),
            "is_default": True,
            
            # Extended fields
            "job_title": extracted_profile.get("job_title", ""),
            "address": json.dumps(extracted_profile.get("address", {})) if extracted_profile.get("address") else None,
            "projects": json.dumps(extracted_profile.get("projects", [])) if extracted_profile.get("projects") else None,
            "awards": json.dumps(extracted_profile.get("awards", [])) if extracted_profile.get("awards") else None,
            "presentations": json.dumps(extracted_profile.get("presentations", [])) if extracted_profile.get("presentations") else None,
            "interests": json.dumps(extracted_profile.get("interests", [])) if extracted_profile.get("interests") else None,
            "skill_categories": json.dumps(extracted_profile.get("skill_categories", [])) if extracted_profile.get("skill_categories") else None
        }
        
        # Check if we have an existing profile for the current user
        existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        
        if existing_profile:
            # Update existing profile
            for key, value in profile_data.items():
                setattr(existing_profile, key, value)
            
            db_profile = existing_profile
        else:
            # Create new profile
            db_profile = CandidateProfile(**profile_data)
            db.add(db_profile)
        
        db.commit()
        db.refresh(db_profile)
        
        return db_profile_to_schema(db_profile)
        
    except Exception as e:
        logger.error(f"Error importing CV: {e}")
        
        # Always clean up the temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # Instead of failing, create a fallback profile with the filename as potential name
        try:
            logger.warning("Creating emergency fallback profile due to error")
            
            # Extract filename-based name if possible
            filename = cv_file.filename or "Unknown"
            potential_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('%20', ' ')
            
            # Create or update profile with emergency fallback data
            existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
            
            profile_data = {
                "user_id": current_user.id,
                "name": potential_name,
                "email": "youremail@example.com",
                "phone": "+48 000 000 000",
                "summary": f"Emergency fallback profile created because your CV could not be imported. Error: {str(e)}",
                "location": "Wrocław, Poland",
                "is_default": True,
                "skills": json.dumps(["Skill 1", "Skill 2", "Skill 3"]),
                "experience": json.dumps([{
                    "company": "Company Name",
                    "position": "Position Title",
                    "start_date": "2020-01",
                    "end_date": "",
                    "current": True,
                    "description": "Please add your job description here."
                }]),
                "education": json.dumps([{
                    "institution": "University Name",
                    "degree": "Degree",
                    "field": "Field of Study",
                    "start_date": "2015-09",
                    "end_date": "2019-06",
                    "current": False
                }])
            }
            
            if existing_profile:
                for key, value in profile_data.items():
                    setattr(existing_profile, key, value)
                db_profile = existing_profile
            else:
                db_profile = CandidateProfile(**profile_data)
                db.add(db_profile)
            
            db.commit()
            db.refresh(db_profile)
            
            logger.info("Successfully created emergency fallback profile")
            return db_profile_to_schema(db_profile)
            
        except Exception as fallback_error:
            # If even the fallback fails, we have no choice but to raise an error
            logger.error(f"Critical error: Even fallback profile creation failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Critical failure during CV import: {str(e)}")
    
    finally:
        # Clean up all temporary files
        
        # Clean up the main temporary file
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")
        
        # Clean up any temporary image files created during PDF processing
        if 'temp_file_path' in locals():
            temp_dir = os.path.dirname(temp_file_path)
            base_name = os.path.basename(temp_file_path)
            try:
                # Find all temporary image files with the pattern of the PDF name
                for filename in os.listdir(temp_dir):
                    if filename.startswith(base_name) and filename.endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join(temp_dir, filename)
                        try:
                            os.unlink(img_path)
                            logger.debug(f"Cleaned up temporary image file: {img_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up temporary image file {img_path}: {e}")
            except Exception as e:
                logger.warning(f"Failed during cleanup of temporary image files: {e}")