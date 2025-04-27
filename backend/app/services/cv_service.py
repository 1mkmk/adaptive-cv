from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.schemas.job import JobCreate
from typing import List, Dict, Any, Optional
import os
import json
import openai
import logging
import re
from datetime import datetime
import base64
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

# Import our LaTeX CV generator
# Import our LaTeX CV generator
from app.services.latex_cv import LaTeXCVGenerator

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_TIMEOUT = 15  # seconds
OPENAI_MAX_RETRIES = 3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVGenerator:
    """Main CV generation service class"""

    def __init__(self, db: Session):
        self.db = db

    # Database operations
    def create_job(self, job: JobCreate) -> Job:
        """Create a new job posting"""
        try:
            db_job = Job(**job.dict())
            self.db.add(db_job)
            self.db.commit()
            self.db.refresh(db_job)
            return db_job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise

    def get_jobs(self, skip: int = 0, limit: int = 10) -> List[Job]:
        """Get list of jobs with pagination"""
        return self.db.query(Job).offset(skip).limit(limit).all()

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a single job by ID"""
        return self.db.query(Job).filter(Job.id == job_id).first()

    def update_job(self, job_id: int, job: JobCreate) -> Optional[Job]:
        """Update an existing job"""
        try:
            db_job = self.get_job(job_id)
            if db_job:
                for key, value in job.dict().items():
                    setattr(db_job, key, value)
                self.db.commit()
                self.db.refresh(db_job)
            return db_job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating job {job_id}: {e}")
            raise

    def delete_job(self, job_id: int) -> bool:
        """Delete a job"""
        try:
            db_job = self.get_job(job_id)
            if db_job:
                self.db.delete(db_job)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting job {job_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(OPENAI_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def extract_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Extract key requirements from job description using OpenAI"""
        if not openai.api_key:
            logger.warning("OpenAI API key not configured")
            return self._default_job_requirements()

        try:
            prompt = self._build_job_requirements_prompt(job_description)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert ATS analyst who extracts requirements from job descriptions."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                request_timeout=OPENAI_TIMEOUT
            )
            
            return self._parse_job_requirements_response(response)
            
        except Exception as e:
            logger.error(f"Error extracting job requirements: {e}")
            return self._default_job_requirements()

    def _build_job_requirements_prompt(self, job_description: str) -> str:
        """Construct the prompt for job requirements extraction"""
        return f"""
        Analyze this job description to extract requirements for ATS screening.
        
        Format the output as JSON with these keys:
        - all_requirements: List of all requirements
        - required_skills: Technical skills required
        - preferred_skills: Nice-to-have skills
        - experience_level: Junior, Mid-level, etc.
        - experience_years: Required years
        - education: Required education
        - key_responsibilities: All responsibilities
        - industry_keywords: Domain-specific terms
        - soft_skills: All soft skills mentioned
        - company_values: Company culture info
        - tools_and_technologies: Specific tools
        - certifications: Required certifications
        - exact_phrases: 10-15 exact phrases to include
        
        Job Description:
        {job_description[:2000]}
        
        Return only JSON without additional text:
        """

    def _parse_job_requirements_response(self, response) -> Dict[str, Any]:
        """Parse the OpenAI response for job requirements"""
        result = response.choices[0].message.content.strip()
        
        # Clean JSON formatting
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
            
        return json.loads(result.strip())

    def _default_job_requirements(self) -> Dict[str, Any]:
        """Default job requirements when extraction fails"""
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

    def get_candidate_profile(self, user_id: int = None) -> Dict[str, Any]:
        """Retrieve candidate profile from database"""
        query = self.db.query(CandidateProfile)
        if user_id:
            candidate = query.filter(CandidateProfile.user_id == user_id).first()
        else:
            candidate = query.first()
            
        if not candidate:
            return {}

        profile = candidate.__dict__
        
        # Parse JSON fields
        for field in ['skills', 'experience', 'education', 'languages', 'certifications', 'projects']:
            if profile.get(field) and isinstance(profile[field], str):
                try:
                    profile[field] = json.loads(profile[field])
                except json.JSONDecodeError:
                    profile[field] = []
        
        # Remove SQLAlchemy internal field
        profile.pop('_sa_instance_state', None)
        
        return profile

    def generate_cv(
        self,
        job_description: str,
        job_id: int = None,
        format: str = "markdown",
        template_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate a tailored CV based on profile and job description
        
        Args:
            job_description: Job description text
            job_id: Optional job ID to save to
            format: Output format ("markdown", "latex", "pdf")
            template_id: Template ID for PDF generation
            
        Returns:
            Dictionary with CV content and metadata
        """
        try:
            # Try PDF generation first if requested
            if format.lower() == "pdf" and job_id is not None:
                try:
                    logger.info(f"Generating PDF CV for job {job_id}")
                    return self.generate_cv_from_template(job_id, template_id)
                except Exception as e:
                    logger.error(f"PDF generation failed: {e}")
                    # Fallback to markdown
                    format = "markdown"

            # Fallback if no OpenAI API
            if not openai.api_key:
                logger.warning("Using fallback CV generator")
                return {
                    "content": self.generate_fallback_cv(job_description),
                    "format": "markdown",
                    "is_fallback": True
                }

            # Get candidate profile
            profile = self.get_candidate_profile()
            if not profile:
                raise ValueError("No candidate profile found")

            # Extract job requirements
            try:
                requirements = self.extract_job_requirements(job_description)
            except Exception as e:
                logger.warning(f"Requirements extraction failed: {e}")
                requirements = self._default_job_requirements()

            # Generate CV content
            cv_content = self._generate_cv_with_openai(profile, job_description, requirements)

            # Save to job if specified
            if job_id is not None and format.lower() != "pdf":
                self._save_cv_to_job(job_id, cv_content)

            return {
                "content": cv_content,
                "format": format,
                "is_fallback": False
            }

        except Exception as e:
            logger.error(f"CV generation error: {e}")
            return {
                "content": self.generate_fallback_cv(job_description),
                "format": "markdown",
                "is_fallback": True,
                "error": str(e)
            }

    def _generate_cv_with_openai(
        self,
        profile: Dict[str, Any],
        job_description: str,
        requirements: Dict[str, Any]
    ) -> str:
        """Generate CV content using OpenAI"""
        prompt = self._build_cv_generation_prompt(profile, job_description, requirements)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional CV writer who creates resumes tailored to job requirements."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
                request_timeout=OPENAI_TIMEOUT
            )
            
            cv_content = response.choices[0].message.content.strip()
            return f"{cv_content}\n\n---\n*CV generated on {datetime.now().strftime('%Y-%m-%d')}*"
            
        except Exception as e:
            logger.error(f"OpenAI CV generation failed: {e}")
            raise

    def _build_cv_generation_prompt(
        self,
        profile: Dict[str, Any],
        job_description: str,
        requirements: Dict[str, Any]
    ) -> str:
        """Construct the prompt for CV generation"""
        skills = ", ".join(profile.get("skills", []))
        
        experience = "\n".join(
            f"- {exp.get('position')} at {exp.get('company')} "
            f"({exp.get('start_date', '')} to {exp.get('end_date', 'Present' if exp.get('current', False) else '')})\n"
            f"  {exp.get('description', '')}"
            for exp in profile.get("experience", [])
        )
        
        education = "\n".join(
            f"- {edu.get('degree')} in {edu.get('field')} from {edu.get('institution')} "
            f"({edu.get('start_date', '')} to {edu.get('end_date', 'Present' if edu.get('current', False) else '')}"
            for edu in profile.get("education", [])
        )
        
        return f"""Create a CV that matches these job requirements:
        
        Job Requirements:
        {json.dumps(requirements, indent=2)[:1000]}
        
        Candidate Profile:
        Name: {profile.get('name')}
        Email: {profile.get('email')}
        Phone: {profile.get('phone', '')}
        Summary: {profile.get('summary', '')[:200]}
        Skills: {skills[:300]}
        
        Experience:
        {experience[:500]}
        
        Education:
        {education[:300]}
        
        Instructions:
        1. Match ALL key requirements from the job
        2. Add relevant skills from the job posting
        3. Structure experience to highlight relevant aspects
        4. Use industry terminology from the job
        5. Format with Summary, Skills, Experience, Education
        6. Ensure ATS compatibility with keywords
        """

    def _save_cv_to_job(self, job_id: int, cv_content: str) -> None:
        """Save generated CV to job record"""
        job = self.get_job(job_id)
        if job:
            job.cv = cv_content
            self.db.commit()
            logger.info(f"Saved CV to job {job_id}")

    def generate_fallback_cv(self, job_description: str) -> str:
        """Generate basic CV without OpenAI"""
        profile = self.get_candidate_profile()
        if not profile:
            return "Error: No candidate profile found"

        keywords = self._extract_keywords(job_description)
        
        # Build CV sections
        sections = [
            self._build_header_section(profile),
            self._build_summary_section(profile),
            self._build_skills_section(profile, keywords),
            self._build_experience_section(profile, keywords),
            self._build_education_section(profile),
            self._build_job_match_section(job_description, keywords)
        ]
        
        return "\n\n".join(filter(None, sections))

    def _build_header_section(self, profile: Dict[str, Any]) -> str:
        """Build the header section of the CV"""
        header = f"# CV: {profile.get('name', 'Your Name')}\n\n## Contact Information\n"
        
        fields = [
            ("Email", profile.get('email')),
            ("Phone", profile.get('phone')),
            ("Location", profile.get('location')),
            ("LinkedIn", profile.get('linkedin')),
            ("Website", profile.get('website'))
        ]
        
        for label, value in fields:
            if value:
                header += f"- {label}: {value}\n"
                
        return header

    def _build_summary_section(self, profile: Dict[str, Any]) -> str:
        """Build the professional summary section"""
        if not profile.get('summary'):
            return ""
            
        return f"## Professional Summary\n{profile['summary']}"

    def _build_skills_section(self, profile: Dict[str, Any], keywords: List[str]) -> str:
        """Build the skills section with keyword matching"""
        skills = profile.get('skills', [])
        if not skills:
            return ""
            
        matched = [s for s in skills if any(k.lower() in s.lower() for k in keywords)]
        others = [s for s in skills if s not in matched]
        
        section = "## Skills\n"
        
        if matched:
            section += "### Key Skills\n" + "\n".join(f"- {s}" for s in matched)
            
        if others:
            section += "\n\n### Additional Skills\n" + "\n".join(f"- {s}" for s in others[:10])
            
        return section

    def _build_experience_section(self, profile: Dict[str, Any], keywords: List[str]) -> str:
        """Build the experience section with keyword highlighting"""
        experiences = profile.get('experience', [])
        if not experiences:
            return ""
            
        section = "## Professional Experience\n"
        
        for exp in experiences:
            position = exp.get('position', '')
            company = exp.get('company', '')
            dates = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present' if exp.get('current', False) else '')}"
            desc = self._highlight_keywords(exp.get('description', ''), keywords)
            
            section += (
                f"### {position} | {company}\n"
                f"*{dates}*\n\n"
                f"{desc}\n\n"
            )
            
        return section

    def _highlight_keywords(self, text: str, keywords: List[str]) -> str:
        """Highlight keywords in text"""
        for keyword in keywords:
            if keyword.lower() in text.lower():
                text = re.sub(
                    f"(?<!\\*)\\b{re.escape(keyword)}\\b(?!\\*)",
                    f"**{keyword}**",
                    text,
                    flags=re.IGNORECASE
                )
        return text

    def _build_education_section(self, profile: Dict[str, Any]) -> str:
        """Build the education section"""
        educations = profile.get('education', [])
        if not educations:
            return ""
            
        section = "## Education\n"
        
        for edu in educations:
            degree = edu.get('degree', '')
            field = edu.get('field', '')
            institution = edu.get('institution', '')
            dates = f"{edu.get('start_date', '')} - {edu.get('end_date', 'Present' if edu.get('current', False) else '')}"
            
            section += (
                f"### {degree} in {field} | {institution}\n"
                f"*{dates}*\n\n"
            )
            
        return section

    def _build_job_match_section(self, job_description: str, keywords: List[str]) -> str:
        """Build the job match analysis section"""
        return (
            "## Job Match Analysis\n"
            f"This CV has been tailored for the following position:\n"
            f"```\n{job_description[:200]}...\n```\n\n"
            f"*Key matching keywords: {', '.join(keywords[:10])}*\n\n"
            f"---\n*CV generated on {datetime.now().strftime('%Y-%m-%d')}*"
        )

    def _extract_keywords(self, job_description: str) -> List[str]:
        """Extract keywords from job description"""
        common_keywords = [
            # Technical skills
            "Python", "JavaScript", "Java", "SQL", "AWS", "Docker", "React", 
            # Business skills
            "Management", "Leadership", "Strategy", "Marketing", "Sales",
            # Soft skills  
            "Communication", "Teamwork", "Problem-solving"
        ]
        
        return [kw for kw in common_keywords if kw.lower() in job_description.lower()] or [
            "experience", "skills", "knowledge"
        ]

    def generate_cv_from_template(
        self,
        job_id: int,
        template_id: str = None,
        model: str = None,
        custom_context: str = None
    ) -> Dict[str, str]:
        """
        Generate CV using LaTeX template
        
        Args:
            job_id: Job ID to generate CV for
            template_id: Template ID to use
            model: Language model to use
            custom_context: Additional context
            
        Returns:
            Dictionary with PDF content and paths
        """
        try:
            logger.info(
                f"Generating CV with template for job {job_id}, "
                f"model={model}, context={'provided' if custom_context else 'not provided'}"
            )
            
            # Get job details
            job = self.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
                
            # Generate content (implementation depends on your LaTeX generator)
            # This is a placeholder - implement according to your LaTeXCVGenerator
            latex_gen = LaTeXCVGenerator(
                template_path="templates",
                output_dir_latex="output/latex",
                output_dir_pdf="output/pdf"
            )
            
            result = latex_gen.generate_cv(
                template_id=template_id or "default",
                job_title=job.title,
                company_name=job.company,
                template_data={
                    "job": job.__dict__,
                    "profile": self.get_candidate_profile(),
                    "custom_context": custom_context
                },
                output_id=str(job_id)
            )
            
            if not result.get("pdf_path"):
                raise ValueError("PDF generation failed")
                
            # Read PDF and create preview
            with open(result["pdf_path"], "rb") as f:
                pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
            preview_content = ""
            if result.get("preview_path"):
                with open(result["preview_path"], "rb") as f:
                    preview_content = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "pdf": pdf_content,
                "preview": preview_content,
                "pdf_path": result["pdf_path"],
                "latex_path": result["latex_path"]
            }
            
        except Exception as e:
            logger.error(f"Template CV generation failed: {e}")
            # Fallback to markdown
            markdown_content = self.generate_cv(
                job.description,
                job_id,
                "markdown"
            ).get("content", "Error generating CV")
            
            return {
                "pdf": None,
                "markdown": markdown_content,
                "error": str(e)
            }

# Add this function export at the bottom of your cv_service.py file
def generate_cv(db, prompt, job_id=None, format="markdown"):
    """
    Generate a CV based on a job description prompt
    This function is used by all the routers
    
    Args:
        db: Database session
        prompt: Job description or prompt
        job_id: Optional job ID to associate with the CV
        format: Output format ("markdown" or "pdf")
        
    Returns:
        Generated CV content
    """
    from app.services.latex_cv import LaTeXCVGenerator
    from app.services.latex_cv.config import TEMPLATE_DIR, LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR
    
    generator = CVGenerator(db)
    # If we have a job ID, retrieve job description
    job_description = None
    if job_id:
        job = generator.get_job(job_id)
        if job:
            job_description = job.description
    
    # Get user profile
    profile = generator.get_candidate_profile(user_id=None)  # Get default profile
    
    # Generate CV content based on format
    if format.lower() == "pdf":
        # For PDF generation, use the LaTeX generator with proper parameters
        latex_generator = LaTeXCVGenerator(
            template_path=TEMPLATE_DIR,
            output_dir_latex=LATEX_OUTPUT_DIR,
            output_dir_pdf=PDF_OUTPUT_DIR
        )
        return latex_generator.generate_cv(prompt, format=format)
    else:
        # Generate Markdown
        requirements = generator.extract_job_requirements(prompt) if prompt else {}
        return generator._generate_cv_with_openai(profile, prompt, requirements)

# Add these functions at the end of your cv_service.py file

def generate_cv_with_template(db, job_id, template_id=None, model=None, custom_context=None, user_id=None, format="pdf"):
    """
    Generate a CV using a specific LaTeX template
    
    Args:
        db: Database session
        job_id: Job ID to associate with the CV
        template_id: ID of the template to use
        model: Language model to use for generation
        custom_context: Additional context for generation
        user_id: User ID for whom to generate the CV
        format: Output format (default: "pdf")
        
    Returns:
        Generated CV content (typically PDF as base64)
    """
    # Get the job if job_id is provided
    job = None
    if job_id:
        job = get_job(db, job_id)
    
    # Import required classes and directories
    from app.services.latex_cv import LaTeXCVGenerator
    from app.services.latex_cv.config import TEMPLATE_DIR, LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR
    import uuid
    
    # Create LaTeX generator with required parameters
    latex_generator = LaTeXCVGenerator(
        template_path=TEMPLATE_DIR,
        output_dir_latex=LATEX_OUTPUT_DIR,
        output_dir_pdf=PDF_OUTPUT_DIR
    )
    
    # Use the new method to generate the CV directly from a template using the job description
    job_description = job.description if job else None
    return latex_generator.generate_with_template(
        template_name=template_id or "default",
        job_description=job_description,
        user_id=user_id,
        format=format
    )


def get_job(db, job_id):
    """
    Get job by ID
    
    Args:
        db: Database session
        job_id: Job ID
        
    Returns:
        Job object or None if not found
    """
    from app.models.job import Job
    return db.query(Job).filter(Job.id == job_id).first()