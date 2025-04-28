"""
LaTeX CV Generator - Main module for LaTeX CV generation.
This module implements the complete CV generation workflow as follows:

1. User chooses template and provides job posting
2. System prepares user profile
3. Job requirements are extracted and profile is matched to job
4. LaTeX template directory is prepared 
5. Template structure is analyzed with AI generating debug.json
6. Template is filled with profile data using OpenAI
7. LaTeX is compiled to PDF
8. Results are returned
"""

import os
import shutil
import subprocess
import tempfile
import logging
import re
import time
import uuid
import base64
import traceback
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Import our custom components
from .template_analyzer import TemplateAnalyzer
from .config import (
    BASE_DIR, ASSETS_DIR, TEMPLATE_DIR, PDF_OUTPUT_DIR,
    LATEX_OUTPUT_DIR, TEMPLATES_EXTRACTED_DIR, TEMPLATES_ZIPPED_DIR)

# Import database models with fully qualified paths
from app.models.candidate import CandidateProfile
from ...database import get_db

logger = logging.getLogger(__name__)

class ProfileProcessor:
    """Process user profiles and job descriptions"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the profile processor"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def extract_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """
        Extract requirements from a job description
        
        Args:
            job_description: Text of job description
            
        Returns:
            Dictionary with extracted requirements
        """
        # Basic extraction without AI
        job_requirements = {
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
        
        # Extract some basic information with regex
        # Required skills section
        skills = []
        skill_keywords = ["python", "javascript", "react", "node", "typescript", "docker", "aws", 
                         "cloud", "azure", "agile", "scrum", "sql", "nosql", "devops", "ci/cd"]
        
        for skill in skill_keywords:
            if re.search(rf'\b{skill}\b', job_description, re.IGNORECASE):
                skills.append(skill)
        
        job_requirements["required_skills"] = skills
        job_requirements["all_requirements"] = skills
        
        # Experience years
        exp_match = re.search(r'(\d+)[+]?\s*(?:years|yrs)(?:\s+of)?\s+experience', job_description, re.IGNORECASE)
        if exp_match:
            job_requirements["experience_years"] = exp_match.group(1) + "+ years"
        
        return job_requirements
    
    def analyze_template_with_openai(self, template_name: str, template_dir: str, 
                                     job_description: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how a template should be filled using OpenAI
        
        Args:
            template_name: Name of template
            template_dir: Directory of template files
            job_description: Job description text
            template_data: User profile data
            
        Returns:
            Dictionary with template filling recommendations
        """
        # Return a basic analysis structure without using OpenAI
        return {
            "template_name": template_name,
            "job_match_score": 70,
            "recommended_sections": ["experience", "skills", "education"],
            "highlighted_skills": template_data.get("skills", [])[:5],
            "customize_profile_summary": True,
            "template_specific_recommendations": {},
            "content_optimization": {
                "summary": "Highlight your relevant experience and skills that match the job requirements.",
                "experience": "Focus on quantifiable achievements and relevant responsibilities.",
                "skills": "List the most relevant technical skills first."
            }
        }

class LaTeXCVGenerator:
    """Main class for LaTeX CV generation using the improved workflow"""
    
    def __init__(self, template_dir: str, openai_api_key: str = None):
        """
        Initialize the LaTeX CV Generator
        
        Args:
            template_dir: Directory containing CV templates
            output_dir: Root directory for output files
            openai_api_key: Optional OpenAI API key (default: environment variable)
        """
        self.template_dir = template_dir
        self.output_dir = os.path.join(ASSETS_DIR, "generated")
        self.output_latex_dir = LATEX_OUTPUT_DIR
        self.output_pdf_dir = PDF_OUTPUT_DIR
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize components
        self.template_analyzer = TemplateAnalyzer()
        self.profile_processor = ProfileProcessor(openai_api_key=self.openai_api_key)
        
        # Check LaTeX installation
        self.latex_installed, self.latex_version = self._check_latex_installation()
        if self.latex_installed:
            logger.info(f"LaTeX installation detected: {self.latex_version}")
        else:
            logger.warning("LaTeX installation not found - PDF generation may fail")

    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        Get list of available CV templates
        
        Returns:
            List of dictionaries with template information
        """
        templates = []
        
        # Scan template directory for templates
        if os.path.exists(self.template_dir):
            for item in os.listdir(self.template_dir):
                template_path = os.path.join(self.template_dir, item)
                if os.path.isdir(template_path):
                    # Check if directory contains .tex files
                    tex_files = [f for f in os.listdir(template_path) if f.endswith('.tex')]
                    
                    if tex_files:
                        template_info = {
                            "id": item,
                            "name": item.replace('_', ' ').title(),
                            "path": template_path,
                            "tex_files": tex_files
                        }
                        
                        # Look for preview image
                        for img_ext in ['.png', '.jpg', '.jpeg']:
                            preview_file = os.path.join(template_path, f"preview{img_ext}")
                            if os.path.exists(preview_file):
                                template_info["preview"] = preview_file
                                break
                        
                        templates.append(template_info)
        
        return templates
        
    def _get_user_profile_from_db(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user profile from database and convert to template data
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with user profile data formatted for the template
        """
        if not user_id:
            logger.warning("No user_id provided, returning default profile")
            return {
                'name': 'Candidate Name',
                'email': 'email@example.com',
                'phone': '+1 234 567 890',
                'address': 'City, Country',
                'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                'skills': [],
                'experience': [],
                'education': [],
                'languages': [],
                'certifications': []
            }
        
        try:
            # Query the database for the user's profile
            db_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
            
            if not db_profile:
                logger.warning(f"No profile found for user {user_id}, returning default profile")
                return {
                    'name': 'Candidate Name',
                    'email': 'email@example.com',
                    'phone': '+1 234 567 890',
                    'address': 'City, Country',
                    'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                    'skills': [],
                    'experience': [],
                    'education': [],
                    'languages': [],
                    'certifications': []
                }
                
            # Convert the database profile to a dictionary for templates
            profile_data = {
                'name': db_profile.name,
                'email': db_profile.email,
                'phone': db_profile.phone or '',
                'summary': db_profile.summary or '',
                'profile_summary': db_profile.summary or '', # Alias for templates
                'location': getattr(db_profile, 'location', ''),
                'linkedin': getattr(db_profile, 'linkedin', ''),
                'website': getattr(db_profile, 'website', ''),
                'photo': getattr(db_profile, 'photo', None),
                'skills': json.loads(db_profile.skills) if db_profile.skills else [],
                'experience': json.loads(db_profile.experience) if db_profile.experience else [],
                'education': json.loads(db_profile.education) if db_profile.education else [],
                'languages': json.loads(db_profile.languages) if hasattr(db_profile, 'languages') and db_profile.languages else [],
                'certifications': json.loads(db_profile.certifications) if hasattr(db_profile, 'certifications') and db_profile.certifications else [],
                'projects': json.loads(db_profile.projects) if hasattr(db_profile, 'projects') and db_profile.projects else [],
                'references': json.loads(db_profile.references) if hasattr(db_profile, 'references') and db_profile.references else [],
                'job_title': getattr(db_profile, 'job_title', ''),
                'address': json.loads(db_profile.address) if hasattr(db_profile, 'address') and db_profile.address else {},
                'interests': json.loads(db_profile.interests) if hasattr(db_profile, 'interests') and db_profile.interests else [],
                'awards': json.loads(db_profile.awards) if hasattr(db_profile, 'awards') and db_profile.awards else [],
                'presentations': json.loads(db_profile.presentations) if hasattr(db_profile, 'presentations') and db_profile.presentations else [],
                'skill_categories': json.loads(db_profile.skill_categories) if hasattr(db_profile, 'skill_categories') and db_profile.skill_categories else [],
                'creativity_levels': json.loads(db_profile.creativity_levels) if hasattr(db_profile, 'creativity_levels') and db_profile.creativity_levels else None,
            }
            
            logger.info(f"Successfully loaded user profile for user {user_id}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Error loading user profile from database: {e}")
            # Return a default profile if there's an error
            return {
                'name': 'Candidate Name',
                'email': 'email@example.com',
                'phone': '+1 234 567 890',
                'address': 'City, Country',
                'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                'skills': [],
                'experience': [],
                'education': [],
                'languages': [],
                'certifications': []
            }

    def generate_cv(self, template_name, job_title, company_name, template_data, output_id, job_description=None):
        """
        Generate CV from template using LaTeX
        
        Args:
            template_name: Name of template to use
            job_title: Job title for directory naming
            company_name: Company name for directory naming
            template_data: User profile data
            output_id: Unique identifier for output files
            job_description: Optional job description text
            
        Returns:
            Dictionary with generation results
        """
        try:
            # 1. Create sanitized output directories
            sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', job_title.lower())[:30]
            sanitized_company = re.sub(r'[^a-zA-Z0-9_]', '_', company_name.lower())[:20]
            output_dirname = f"{sanitized_name}_{sanitized_company}_{time.strftime('%Y%m%d')}_{output_id[:8]}"
            
            latex_output_dir = os.path.join(self.output_latex_dir, output_dirname)
            pdf_output_dir = os.path.join(self.output_pdf_dir, output_dirname)
            
            # Create output directories
            os.makedirs(latex_output_dir, exist_ok=True)
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            # 2. Find template directory - Fix: Look in templates_extracted subdirectory
            template_path = os.path.join(self.template_dir, "templates_extracted", template_name)
            if not os.path.exists(template_path):
                # Fallback to direct path if not found in templates_extracted
                template_path = os.path.join(self.template_dir, template_name)
                if not os.path.exists(template_path):
                    raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
            
            # Save original profile data to profile.json
            profile_path = os.path.join(latex_output_dir, 'profile.json')
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)
            logger.info(f"Saved original profile data to {profile_path}")
            
            # 3. Process profile data with job description if available
            if job_description:
                # Step 3.1: Extract job requirements and save as JSON
                job_requirements = self.profile_processor.extract_job_requirements(job_description)
                
                # Step 3.2: Save original profile data from database to profile.json
                profile_path = os.path.join(latex_output_dir, 'profile.json')
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)
                logger.info(f"Saved user profile data to {profile_path}")
                
                # Step 3.3: Save job requirements for analysis and debugging
                requirements_path = os.path.join(latex_output_dir, 'job_requirements.json')
                with open(requirements_path, 'w', encoding='utf-8') as f:
                    json.dump(job_requirements, f, indent=2)
                logger.info(f"Saved job requirements analysis to {requirements_path}")
                
                # Step 3.4: Analyze how the template should be filled based on job requirements
                template_analysis = self.profile_processor.analyze_template_with_openai(
                    template_name=template_name,
                    template_dir=template_path,
                    job_description=job_description,
                    template_data=template_data
                )
                
                # Step 3.5: Save template analysis
                analysis_path = os.path.join(latex_output_dir, 'template.json')
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(template_analysis, f, indent=2)
                logger.info(f"Saved template analysis to {analysis_path}")
                
                # Use original data for template filling without AI modification
                processed_data = template_data
            else:
                # If no job description, just use the profile data as is
                processed_data = template_data
                
                # Still save the profile.json for consistency
                profile_path = os.path.join(latex_output_dir, 'profile.json')
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)
                logger.info(f"Saved user profile data to {profile_path}")
            
            # 4. Analyze and fill template
            template_result = self.template_analyzer.fill_template(
                template_dir=template_path,
                output_dir=latex_output_dir,
                template_data=processed_data,
                job_description=job_description,
                template_name=template_name
            )
            
            # Save debug information from template analysis
            debug_path = os.path.join(latex_output_dir, 'debug.json')
            if not os.path.exists(debug_path):
                # If template analyzer didn't create it, generate a basic version
                self.template_analyzer.generate_debug_report(
                    template_result.get("template_info", {}),
                    os.path.join(latex_output_dir, 'debug.tex')
                )
            
            # 5. Process user's photo if it exists
            if 'photo' in processed_data and processed_data['photo']:
                photo_path = processed_data['photo']
                if os.path.exists(photo_path):
                    # Create photos directory
                    photos_dir = os.path.join(latex_output_dir, 'photos')
                    os.makedirs(photos_dir, exist_ok=True)
                    
                    # Copy photo with different names for compatibility
                    for name in ['photo', 'profile', 'picture']:
                        try:
                            photo_target = os.path.join(latex_output_dir, f'{name}.jpg')
                            shutil.copy2(photo_path, photo_target)
                            
                            photo_target_dir = os.path.join(photos_dir, f'{name}.jpg')
                            shutil.copy2(photo_path, photo_target_dir)
                        except Exception as e:
                            logger.warning(f"Failed to copy photo as {name}: {e}")
            
            # 6. Compile LaTeX to PDF
            success = self._compile_latex(latex_output_dir)
            
            if success:
                # Copy PDF to output directory
                pdf_path = os.path.join(latex_output_dir, 'cv.pdf')
                pdf_output_path = os.path.join(pdf_output_dir, 'cv.pdf')
                shutil.copy2(pdf_path, pdf_output_path)
                
                # Generate preview image
                self._generate_preview(pdf_output_path, latex_output_dir)
                
                return {
                    'success': True,
                    'latex_path': latex_output_dir,
                    'pdf_path': pdf_output_path,
                    'output_id': output_id
                }
            else:
                logger.error("LaTeX compilation failed")
                raise HTTPException(status_code=500, detail="Failed to compile LaTeX document")
                
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating CV: {str(e)}")

    def _check_latex_installation(self):
        """Check if LaTeX is installed and return version info"""
        try:
            version_check = subprocess.run(["pdflatex", "--version"], 
                                          capture_output=True, text=True, timeout=5)
            if version_check.returncode == 0:
                version = version_check.stdout.splitlines()[0].strip()
                return True, version
            return False, None
        except Exception as e:
            logger.error(f"Error checking LaTeX installation: {e}")
            return False, None

    def _compile_latex(self, output_dir):
        """
        Compile LaTeX document to PDF
        
        Args:
            output_dir: Directory containing LaTeX files
            
        Returns:
            Boolean indicating success
        """
        try:
            # Save current directory
            orig_dir = os.getcwd()
            os.chdir(output_dir)
            
            # Check if main CV file exists
            if not os.path.exists('cv.tex'):
                # Find any TeX file that might be the main file
                tex_files = [f for f in os.listdir('.') if f.endswith('.tex')]
                if not tex_files:
                    logger.error("No .tex files found for compilation")
                    return False
                
                # Try to find a main file by looking for document environment
                main_file = None
                for tex_file in tex_files:
                    with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '\\begin{document}' in content and '\\end{document}' in content:
                            main_file = tex_file
                            break
                
                if not main_file:
                    # Use the first .tex file if no better candidate
                    main_file = tex_files[0]
                
                # Create a symlink to the main file
                logger.info(f"Using {main_file} as main LaTeX file")
                shutil.copy2(main_file, 'cv.tex')
            
            # Create log files
            log_file = os.path.join(output_dir, "compile_log.txt")
            error_log_file = os.path.join(output_dir, "compile_error.txt")
            
            # Run pdflatex command
            logger.info(f"Compiling LaTeX document in {output_dir}")
            
            # Command with options
            pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", "cv.tex"]
            
            # First run
            result = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
            
            # Save log
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            if result.stderr:
                with open(error_log_file, "w", encoding="utf-8") as f:
                    f.write(result.stderr)
            
            # If successful, run a second time to resolve references
            if os.path.exists("cv.pdf"):
                result2 = subprocess.run(pdflatex_cmd, capture_output=True, text=True)
                # Append to logs
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write("\n\n--- SECOND RUN ---\n\n")
                    f.write(result2.stdout)
                if result2.stderr:
                    with open(error_log_file, "a", encoding="utf-8") as f:
                        f.write("\n\n--- SECOND RUN ---\n\n")
                        f.write(result2.stderr)
            
            # Check for success
            success = os.path.exists("cv.pdf")
            
            if not success:
                # Try fallback if available
                if os.path.exists("fallback.tex"):
                    logger.info("Attempting to compile fallback.tex")
                    fallback_cmd = ["pdflatex", "-interaction=nonstopmode", "fallback.tex"]
                    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("\n\n--- FALLBACK TEMPLATE ---\n\n")
                        f.write(fallback_result.stdout)
                    
                    if fallback_result.returncode == 0 and os.path.exists("fallback.pdf"):
                        # Rename fallback.pdf to cv.pdf
                        os.rename("fallback.pdf", "cv.pdf")
                        logger.info("Successfully compiled fallback template")
                        success = True
                else:
                    # Extract error details from log
                    error_lines = []
                    for line in result.stdout.splitlines():
                        if ":" in line and ".tex" in line and any(err in line.lower() for err in ["error", "fatal"]):
                            error_lines.append(line)
                    
                    if error_lines:
                        error_details = "\n".join(error_lines)
                        logger.error(f"LaTeX compilation errors:\n{error_details}")
                    else:
                        logger.error("LaTeX compilation failed without specific error messages")
            
            return success
            
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {str(e)}")
            return False
        finally:
            # Return to original directory
            os.chdir(orig_dir)

    def _generate_preview(self, pdf_path, output_dir):
        """
        Generate preview image from PDF
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save preview
            
        Returns:
            Path to preview image or None if failed
        """
        try:
            preview_path = os.path.join(output_dir, 'preview.jpg')
            
            # Try different tools for PDF conversion
            tools = [
                ['pdftoppm', '-jpeg', '-singlefile', '-scale-to', '800', pdf_path, os.path.join(output_dir, 'preview')],
                ['convert', '-density', '150', f'{pdf_path}[0]', '-quality', '90', '-resize', '800x', preview_path]
            ]
            
            for tool_cmd in tools:
                try:
                    result = subprocess.run(tool_cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(preview_path):
                        logger.info(f"Generated preview using {tool_cmd[0]}")
                        return preview_path
                except Exception as e:
                    logger.warning(f"Failed to use {tool_cmd[0]} for preview: {e}")
            
            logger.warning("Failed to generate preview image")
            return None
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return None

    def generate_with_template(self, template_name, job_description, user_id=None, format="pdf"):
        """
        Generate a CV using a template and job description
        
        Args:
            template_name: Name of the template to use
            job_description: Job description to use for CV generation
            user_id: Optional user ID to fetch profile
            format: Output format ("pdf" or "latex")
            
        Returns:
            Dictionary with generated CV information
        """
        try:
            logger.info(f"Generating CV with template '{template_name}' from job description")
            
            # 1. Prepare basic resources
            output_id = str(uuid.uuid4())
            
            # Extract job title and company from description
            job_title = "Position"
            company_name = "Company"
            
            if job_description:
                lines = job_description.strip().split('\n')
                if lines:
                    # First line might contain job title
                    first_line = lines[0].strip()
                    if len(first_line) < 100:
                        job_title = first_line
                    
                    # Try to find company name
                    for i in range(min(5, len(lines))):
                        line = lines[i].lower()
                        if "company:" in line or "at " in line or "for " in line:
                            company_match = re.search(r'(?:company:|at|for)\s+([A-Za-z0-9\s&]+)', line, re.IGNORECASE)
                            if company_match:
                                company_name = company_match.group(1).strip()
                                break
            
            # 2. Get profile data from the database if user_id is provided
            db = next(get_db())
            if user_id:
                logger.info(f"Fetching profile data from database for user {user_id}")
                template_data = self._get_user_profile_from_db(db, user_id)
            else:
                logger.info("No user_id provided, using default profile data")
                # Use default profile if no user_id
                template_data = {
                    'name': 'Candidate Name',
                    'email': 'email@example.com',
                    'phone': '+1 234 567 890',
                    'address': 'City, Country',
                    'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                    'skills': [],
                    'experience': [],
                    'education': [],
                    'languages': [],
                    'certifications': []
                }
            
            # 3. Create output directories for the generated files
            sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', job_title.lower())[:30]
            sanitized_company = re.sub(r'[^a-zA-Z0-9_]', '_', company_name.lower())[:20]
            output_dirname = f"{sanitized_name}_{sanitized_company}_{time.strftime('%Y%m%d')}_{output_id[:8]}"
            
            latex_output_dir = os.path.join(self.output_latex_dir, output_dirname)
            pdf_output_dir = os.path.join(self.output_pdf_dir, output_dirname)
            
            # Create output directories
            os.makedirs(latex_output_dir, exist_ok=True)
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            # 4. Find template directory
            template_path = os.path.join(self.template_dir, "templates_extracted", template_name)
            if not os.path.exists(template_path):
                # Fallback to direct path if not found in templates_extracted
                template_path = os.path.join(self.template_dir, template_name)
                if not os.path.exists(template_path):
                    raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
            
            # 5. Generate AI template analysis 
            if job_description:
                try:
                    # Extract job requirements
                    job_requirements = self.profile_processor.extract_job_requirements(job_description)
                    
                    # Save job requirements for debug purposes
                    requirements_path = os.path.join(latex_output_dir, 'job_requirements.json')
                    with open(requirements_path, 'w', encoding='utf-8') as f:
                        json.dump(job_requirements, f, indent=2)
                    
                    # Import the generate_ai_template_analysis function from template_analyzer
                    from .template_analyzer.openai_analyzer import generate_ai_template_analysis
                    
                    # Analyze template directory to get template_info
                    template_info = self.template_analyzer.analyze_template_directory(template_path)
                    
                    # Generate comprehensive AI analysis
                    ai_analysis = generate_ai_template_analysis(
                        template_info=template_info,
                        job_description=job_description,
                        template_data=template_data,
                        template_name=template_name,
                        output_dir=latex_output_dir
                    )
                    
                    logger.info("Successfully analyzed template with AI")
                    
                except Exception as e:
                    logger.error(f"Error analyzing template with AI: {e}")
                    # Continue without AI analysis if it fails
            
            # 6. Generate CV with the profile data and template
            result = self.generate_cv(
                template_name=template_name,
                job_title=job_title,
                company_name=company_name,
                template_data=template_data,
                output_id=output_id,
                job_description=job_description
            )
            
            # 7. Return results based on requested format
            if format.lower() == "latex":
                return {
                    "latex_path": result["latex_path"],
                    "output_id": output_id
                }
            else:
                # Return PDF content for response
                pdf_path = result["pdf_path"]
                
                with open(pdf_path, "rb") as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # Try to get preview
                preview_content = ""
                preview_path = os.path.join(result["latex_path"], "preview.jpg")
                if os.path.exists(preview_path):
                    with open(preview_path, "rb") as f:
                        preview_content = base64.b64encode(f.read()).decode('utf-8')
                
                return {
                    "pdf": pdf_content,
                    "preview": preview_content,
                    "pdf_path": pdf_path,
                    "latex_path": result["latex_path"],
                    "output_id": output_id
                }
                
        except HTTPException as http_e:
            # Pass through HTTP exceptions with status codes
            raise http_e
        except Exception as e:
            # Handle other errors
            error_msg = f"Error in generate_with_template: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)