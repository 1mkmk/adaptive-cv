"""
Core LaTeX CV Generator implementation, refactored into a more modular structure.
"""

import os
import shutil
import subprocess
import tempfile
import logging
import re
import time
import uuid
import traceback
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from .config import (
    BASE_DIR, ASSETS_DIR, TEMPLATE_DIR, 
    LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR,
    TEMPLATES_EXTRACTED_DIR, TEMPLATES_ZIPPED_DIR
)
from .compilation import LaTeXCompiler
from .template_utils import get_available_templates
from .document_builder import LaTeXDocumentBuilder
from .profile_processor import ProfileProcessor
from .template_analyzer import TemplateAnalyzer

logger = logging.getLogger(__name__)

class LaTeXCVGenerator:
    """Service for generating LaTeX documents and compiling to PDF"""
    
    def __init__(self, template_path=None, output_dir_latex=None, output_dir_pdf=None):
        """Initialize the LaTeX CV Generator with template path and output directories"""
        self.template_path = template_path or TEMPLATE_DIR
        self.output_dir_latex = output_dir_latex or LATEX_OUTPUT_DIR
        self.output_dir_pdf = output_dir_pdf or PDF_OUTPUT_DIR
        
        # Create component instances
        self.document_builder = LaTeXDocumentBuilder(template_path)
        self.profile_processor = ProfileProcessor()
        self.template_analyzer = TemplateAnalyzer()
        
        # Ensure output directories exist
        os.makedirs(self.output_dir_latex, exist_ok=True)
        os.makedirs(self.output_dir_pdf, exist_ok=True)
        
        # Check for LaTeX installation at initialization
        self.latex_installed, self.latex_version = LaTeXCompiler.check_latex_installation()
        if self.latex_installed:
            logger.info(f"Using local LaTeX compilation: {self.latex_version}")
        else:
            logger.warning("LaTeX installation not found. PDF generation may fail.")
    
    def compile_latex_locally(self, template_dir, main_file=None):
        """
        Compile LaTeX document locally
        
        Args:
            template_dir: Directory containing LaTeX files
            main_file: Path to main LaTeX file (relative to template_dir)
            
        Returns:
            Boolean indicating if compilation was successful
        """
        if main_file:
            latex_file = os.path.join(template_dir, main_file)
        else:
            latex_file = os.path.join(template_dir, "cv.tex")
            
        return LaTeXCompiler.compile_latex(template_dir, latex_file)
    
    def generate_debug_json(self, template_info, job_description, template_data, job_title, company_name, template_name):
        """
        Generate debug JSON using OpenAI to analyze template, job requirements and profile match
        
        Args:
            template_info: Template analysis information
            job_description: Job description text
            template_data: User profile data
            job_title: Job title
            company_name: Company name
            template_name: Template name
            
        Returns:
            JSON object with comprehensive debug information
        """
        try:
            import openai
            
            # Extract job requirements using the profile processor
            job_requirements = self.profile_processor.extract_job_requirements(job_description)
            
            # Set OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OpenAI API key not available, skipping debug JSON generation")
                # Return basic template info without AI-enhanced content
                return {
                    "template": {
                        "path": template_info.get('path'),
                        "structure": template_info.get('structure', 'unknown'),
                        "main_files": template_info.get("main_files", []),
                        "support_files": template_info.get("support_files", [])
                    },
                    "detected_fields": template_info.get("detected_fields", {}),
                    "job_match": {
                        "template_name": template_name,
                        "job_title": job_title,
                        "company_name": company_name,
                        "candidate_data": template_data,
                        "job_analysis": {"matched_skills": [], "missing_skills": [], "highlighted_experience": []}
                    }
                }
                
            openai.api_key = openai_api_key
            
            # Define prompts for creating the debug analysis
            system_prompt = """You are an AI assistant specialized in analyzing templates, job descriptions, and candidate profiles for CV generation. 
            Your task is to analyze a LaTeX template, a job description, and a candidate profile, producing a comprehensive debug.json file that contains:
            
            1. Complete template analysis including all available fields, structure, customization options, and LaTeX commands
            2. Detailed job requirements extracted from the job description
            3. Analysis of how well the candidate's profile matches the job requirements
            4. Identification of the candidate's strengths and weaknesses relative to the job
            5. Suggestions for improving the profile to better match the job
            6. Template-specific recommendations for highlighting key qualifications
            
            Your output should be a single, well-structured JSON object with all this information.
            """
            
            user_prompt = f"""
            Create a comprehensive debug.json file for a CV generation system with the following inputs:
            
            TEMPLATE INFO:
            {json.dumps(template_info, indent=2)}
            
            JOB DESCRIPTION:
            {job_description[:2000] if job_description else "No job description provided."}
            
            CANDIDATE PROFILE DATA:
            {json.dumps(template_data, indent=2)}
            
            JOB REQUIREMENTS (AI EXTRACTED):
            {json.dumps(job_requirements, indent=2) if job_requirements else "No job requirements extracted."}
            
            TEMPLATE NAME: {template_name}
            JOB TITLE: {job_title}
            COMPANY NAME: {company_name}
            
            FORMAT YOUR RESPONSE AS A SINGLE, WELL-STRUCTURED JSON OBJECT with these main sections:
            1. "template" - Information about the template structure, including:
               * path, structure, main_files, support_files (from the input)
               * template_analysis: An AI-generated analysis of template strengths, weaknesses, and optimal uses
               * customization_options: Key ways this template can be customized
               * section_mapping: How template sections map to candidate data fields
            
            2. "detected_fields" - Detailed analysis of the fields detected in the template, including:
               * commands: LaTeX commands available in the template
               * environments: LaTeX environments used in the template
               * custom_commands: Custom LaTeX commands defined in the template
               * placeholders: Placeholder text found in the template
               * ai_field_analysis: AI-generated suggestions for using these fields effectively
            
            3. "job_match" - Comprehensive analysis of how the candidate profile matches the job requirements, including:
               * template_name, job_title, company_name
               * candidate_data (the cleaned profile data)
               * job_analysis containing:
                 - extracted_requirements (detailed breakdown of job requirements)
                 - profile_enhancement (analysis of matches, gaps, and improvement suggestions)
                 - template_specific_recommendations (how to use this specific template to highlight key qualifications)
            
            Return ONLY a valid JSON object without any additional text or explanation.
            """
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    debug_data = json.loads(json_str)
                    return debug_data
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from AI debug response")
                    # Return basic info if JSON parsing fails
                    return {
                        "template": {
                            "path": template_info.get('path'),
                            "structure": template_info.get('structure', 'unknown'),
                            "main_files": template_info.get("main_files", []),
                            "support_files": template_info.get("support_files", [])
                        },
                        "detected_fields": template_info.get("detected_fields", {}),
                        "error": "Failed to parse AI-generated debug JSON"
                    }
            else:
                logger.warning("No JSON found in AI debug response")
                return {
                    "template": {
                        "path": template_info.get('path'),
                        "structure": template_info.get('structure', 'unknown'),
                        "main_files": template_info.get("main_files", []),
                        "support_files": template_info.get("support_files", [])
                    },
                    "detected_fields": template_info.get("detected_fields", {}),
                    "error": "No JSON found in AI response"
                }
                
        except Exception as e:
            logger.warning(f"Error generating debug JSON: {str(e)}")
            # Return basic info if an error occurs
            return {
                "template": {
                    "path": template_info.get('path'),
                    "structure": template_info.get('structure', 'unknown'),
                    "main_files": template_info.get("main_files", []),
                    "support_files": template_info.get("support_files", [])
                },
                "detected_fields": template_info.get("detected_fields", {}),
                "error": f"Error generating debug JSON: {str(e)}"
            }
    
    def generate_cv(self, template_name, job_title, company_name, template_data, output_id, job_description=None):
        """
        Generate a LaTeX CV for a job, prepare for compilation
        
        Args:
            template_name: Name of the template to use
            job_title: Title of the job
            company_name: Name of the company
            template_data: Dictionary with CV data
            output_id: Unique ID for the output files
            job_description: Optional job description text
            
        Returns:
            Dictionary with paths to generated files
        """
        try:
            # Create output directories
            sanitized_company = re.sub(r'[^a-z0-9]', '_', company_name.lower())
            sanitized_jobtitle = re.sub(r'[^a-z0-9]', '_', job_title.lower())
            output_folder_name = f"{sanitized_jobtitle}_{sanitized_company}_{time.strftime('%Y%m%d')}_{output_id[:8]}"
            
            latex_output_dir = os.path.join(self.output_dir_latex, output_folder_name)
            pdf_output_dir = os.path.join(self.output_dir_pdf, output_folder_name)
            
            os.makedirs(latex_output_dir, exist_ok=True)
            os.makedirs(os.path.join(latex_output_dir, "files"), exist_ok=True)
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            # Get the list of available templates
            templates = get_available_templates()
            
            # Find the selected template
            template_info = next((template for template in templates if template["id"] == template_name), None)
            
            if not template_info:
                logger.warning(f"Template '{template_name}' not found. Using first available template.")
                if templates:
                    template_info = templates[0]
                else:
                    raise ValueError("No templates available")
            
            # Path to template files
            template_path = template_info["path"]
            
            # Handle zipped templates if needed
            if "zip_file" in template_info:
                import zipfile
                zip_file = os.path.join(TEMPLATES_ZIPPED_DIR, template_info["zip_file"])
                extract_dir = os.path.join(TEMPLATES_EXTRACTED_DIR, template_name)
                
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir, exist_ok=True)
                    
                    # Extract the ZIP file
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                
                # Update template path to the extracted directory
                template_path = extract_dir
            
            # Create files directory with content from template
            files_dir = os.path.join(latex_output_dir, "files")
            
            # Copy template files to the files directory
            if os.path.isdir(template_path):
                for item in os.listdir(template_path):
                    item_path = os.path.join(template_path, item)
                    if os.path.isfile(item_path):
                        shutil.copy2(item_path, files_dir)
            
            # Use template analyzer to analyze the template and fill with data
            analyzer_result = self.template_analyzer.fill_template(files_dir, latex_output_dir, template_data)
            
            # Get the main file identified by the analyzer
            main_file = analyzer_result.get("main_file", "cv.tex")
            if not main_file:
                # Fallback to LaTeX document builder if analyzer couldn't fill the template
                logger.warning("Template analyzer couldn't identify main file, falling back to document builder")
                latex_file = self.document_builder.create_latex_file(template_data, latex_output_dir, files_dir)
                main_file = os.path.basename(latex_file)
            
            # Generate AI-powered debug JSON with comprehensive analysis of template, job, and profile
            debug_data = self.generate_debug_json(
                analyzer_result["template_info"],
                job_description,
                template_data,
                job_title,
                company_name,
                template_name
            )
            
            # Write the debug JSON file
            debug_json_path = os.path.join(latex_output_dir, "debug.json")
            with open(debug_json_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            
            # Create a minimal debug.tex for backward compatibility
            with open(os.path.join(latex_output_dir, "debug.tex"), 'w', encoding='utf-8') as f:
                f.write("% Template Analysis Debug Report - See debug.json for full details\n\n")
                f.write(f"% Template path: {analyzer_result['template_info'].get('path')}\n")
                f.write(f"% Debug data stored in: debug.json\n")
            
            # Create the return data
            result = {
                "template_name": template_name,
                "job_title": job_title,
                "company_name": company_name,
                "latex_dir": latex_output_dir,
                "pdf_dir": pdf_output_dir,
                "latex_file": os.path.join(latex_output_dir, main_file),
                "pdf_file": os.path.join(pdf_output_dir, "cv.pdf"),
                "output_id": output_id,
                "analyzer_result": analyzer_result
            }
            
            # Compile to PDF
            if self.latex_installed:
                success = self.compile_latex_locally(latex_output_dir, main_file)
                if success:
                    # Copy the PDF file to the PDF output directory
                    pdf_file = os.path.join(latex_output_dir, os.path.splitext(main_file)[0] + ".pdf")
                    if os.path.exists(pdf_file):
                        shutil.copy2(pdf_file, os.path.join(pdf_output_dir, "cv.pdf"))
                        result["compiled"] = True
                    else:
                        result["compiled"] = False
                        result["error"] = "PDF file not found after compilation"
                else:
                    result["compiled"] = False
                    result["error"] = "LaTeX compilation failed"
            else:
                result["compiled"] = False
                result["error"] = "LaTeX not installed"
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating CV: {str(e)}")
            traceback.print_exc()
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "template_name": template_name
            }
    
    def generate_with_template(self, template_name, job_description, user_id=None, format="pdf"):
        """
        Generate a CV using a template and job description
        
        Args:
            template_name: Name of the template to use
            job_description: Job description to use for CV generation
            user_id: Optional user ID
            format: Output format ("pdf" or "latex")
            
        Returns:
            Dictionary with generated CV information
        """
        # Import required modules at the function level to avoid scope issues
        try:
            logger.info(f"Generating CV with template {template_name} from job description")
            
            # Create a unique output ID
            output_id = str(uuid.uuid4())
            
            # Extract job title and company from description if possible
            job_title = "Position"
            company_name = "Company"
            
            # Try to extract job title from the first line of job description
            if job_description:
                lines = job_description.strip().split('\n')
                if lines:
                    # First line might contain job title
                    first_line = lines[0].strip()
                    if len(first_line) < 100:  # Reasonable job title length
                        job_title = first_line
                    
                    # Try to find company name in first few lines
                    for i in range(min(5, len(lines))):
                        line = lines[i].lower()
                        if "company:" in line or "at" in line or "for" in line:
                            company_match = re.search(r'(?:company:|at|for)\s+([A-Za-z0-9\s&]+)', line, re.IGNORECASE)
                            if company_match:
                                company_name = company_match.group(1).strip()
                                break
            
            # Process job description to extract key information
            # Create a default requirements dictionary
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
            
            # Try to get user profile data if provided
            from app.services.cv_service import CVGenerator
            from app.database import SessionLocal
            
            # Default template data
            template_data = {
                'name': 'Candidate Name',
                'email': 'email@example.com',
                'phone': '+1 234 567 890',
                'address': 'City, Country',
                'profile_summary': 'Experienced professional with expertise matching the job requirements.',
                'photo': None,
                'experience': [],
                'education': [],
                'skills': [],
                'languages': [],
                'certifications': []
            }
            
            # Try to get actual user profile
            try:
                # Create a database session
                db = SessionLocal()
                
                # Create CV generator and get profile
                cv_gen = CVGenerator(db)
                
                # Handle potential errors with profile loading
                try:
                    user_profile = cv_gen.get_candidate_profile(user_id)
                    # Check if the user_profile is valid
                    if isinstance(user_profile, str):
                        logger.warning(f"User profile returned as string: {user_profile}")
                        user_profile = {}
                    # Make sure it's a dict 
                    elif not isinstance(user_profile, dict):
                        logger.warning(f"User profile returned in unexpected format: {type(user_profile)}")
                        user_profile = {}
                except Exception as e:
                    logger.warning(f"Error getting user profile from CV generator: {e}")
                    user_profile = {}
                
                # Close database session
                db.close()
                
                # Update template data with user profile if available
                if user_profile:
                    logger.info(f"Using user profile data for CV generation")
                    
                    # Process user profile to update template data
                    template_data = self.profile_processor.process_user_profile(user_profile, template_data)
            except Exception as e:
                logger.warning(f"Could not load user profile: {e}")
                # Continue with default data
            
            # If we have a job description, use it to generate better template data
            if job_description:
                try:
                    # Generate CV content based on job description using external service (OpenAI)
                    template_data = self.profile_processor.process_with_ai(job_description, template_data)
                except Exception as e:
                    logger.warning(f"Error using AI to process CV: {e}")
            
            # Generate the CV with the template and data, passing the job description
            result = self.generate_cv(template_name, job_title, company_name, template_data, output_id, job_description)
            
            # Add format-specific information
            if format.lower() == "pdf":
                result["format"] = "pdf"
                pdf_file = result.get("pdf_file")
                if pdf_file and os.path.exists(pdf_file):
                    result["file_url"] = f"/api/cv/pdf/{output_id}"
                    result["download_url"] = f"/api/cv/download/{output_id}"
                else:
                    result["file_url"] = None
                    result["download_url"] = None
                    result["error"] = result.get("error", "PDF generation failed")
            else:
                result["format"] = "latex"
                result["file_url"] = f"/api/cv/latex/{output_id}"
                result["download_url"] = f"/api/cv/download/{output_id}/latex"
            
            return result
        
        except Exception as e:
            logger.error(f"Error in generate_with_template: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")