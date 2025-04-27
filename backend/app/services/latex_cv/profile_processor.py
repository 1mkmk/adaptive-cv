"""
Profile processor module for LaTeX CV generator.

This module is responsible for processing user profiles and job data.
"""

import re
import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProfileProcessor:
    """Processes and cleans profile data for LaTeX CV generation"""
    
    def __init__(self, openai_api_key=None):
        """Initialize the profile processor"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def process_user_profile(self, user_profile, template_data):
        """
        Process user profile to update template data
        
        Args:
            user_profile: Raw user profile data
            template_data: Template data to update
            
        Returns:
            Updated template data
        """
        # Common placeholder patterns that should be ignored
        placeholder_patterns = [
            r'{\s*"line1":', r'example\.com',
            r'placeholder', r'not provided', 
            r'your name', r'your email', r'your phone',
            r'short project title', r'build a project',
            r'quantified success', r'quanti[^\s]*ed success',
            r'try it here', r'sample bullet',
            r'spans two lines', r'won an award',
            r'a, b, and c', r'hiring search tool',
            r'over 25000 people', r'saved and shared'
        ]
        
        # Update basic information - only include non-empty values
        basic_fields = {
            'name': 'name',
            'email': 'email',
            'phone': 'phone',
            'address': 'address',
            'summary': 'profile_summary',
            'photo_path': 'photo',
            'website': 'website',
            'linkedin': 'linkedin',
            'github': 'github'
        }
        
        # Only include fields that have actual content
        for profile_field, template_field in basic_fields.items():
            value = user_profile.get(profile_field)
            
            # Check if value exists and is not just whitespace
            if value and (not isinstance(value, str) or value.strip()):
                # For strings, check for placeholder patterns
                if isinstance(value, str):
                    # Check if it matches any placeholder pattern
                    if not any(re.search(pattern, value.lower()) for pattern in placeholder_patterns):
                        template_data[template_field] = value
                else:
                    template_data[template_field] = value
        
        # Copy complex fields - only include fields that exist and have content
        for field in ['experience', 'education', 'skills', 'languages', 'certifications', 'projects']:
            if field in user_profile and user_profile[field]:
                # Filter out items with missing required fields and placeholders
                if field == 'experience':
                    template_data[field] = [
                        exp for exp in user_profile[field] 
                        if exp.get('title') and exp.get('company') and
                        self.is_not_placeholder(exp.get('title')) and 
                        self.is_not_placeholder(exp.get('company'))
                    ]
                elif field == 'education':
                    template_data[field] = [
                        edu for edu in user_profile[field]
                        if edu.get('degree') and edu.get('institution') and
                        self.is_not_placeholder(edu.get('degree')) and 
                        self.is_not_placeholder(edu.get('institution'))
                    ]
                elif field == 'skills':
                    template_data[field] = [
                        skill for skill in user_profile[field]
                        if skill.get('name') and self.is_not_placeholder(skill.get('name'))
                    ]
                elif field == 'languages':
                    template_data[field] = [
                        lang for lang in user_profile[field]
                        if lang.get('name') and lang.get('level') and
                        self.is_not_placeholder(lang.get('name')) and 
                        self.is_not_placeholder(lang.get('level'))
                    ]
                elif field == 'certifications':
                    template_data[field] = [
                        cert for cert in user_profile[field]
                        if cert.get('name') and self.is_not_placeholder(cert.get('name'))
                    ]
                elif field == 'projects':
                    template_data[field] = [
                        proj for proj in user_profile[field]
                        if proj.get('name') and self.is_not_placeholder(proj.get('name')) and
                        proj.get('description') and self.is_not_placeholder(proj.get('description'))
                    ]
                
                # If after filtering, the list is empty, don't include it
                if field in template_data and not template_data[field]:
                    del template_data[field]
        
        return template_data
    
    def extract_job_requirements(self, job_description):
        """
        Use AI to extract key requirements from a job description
        
        Args:
            job_description: The job description text
            
        Returns:
            Dictionary with extracted requirements
        """
        try:
            import openai
            
            # Set OpenAI API key
            if not self.openai_api_key:
                logger.warning("OpenAI API key not available, skipping job requirement extraction")
                return {}
                
            openai.api_key = self.openai_api_key
            
            # Define prompt for job requirement extraction
            system_prompt = """You are an AI assistant specialized in analyzing job descriptions and extracting key requirements for CV optimization.
            
            Extract the following information from the job description:
            1. Required technical skills (must-have skills)
            2. Preferred/desired technical skills (nice-to-have skills)
            3. Experience level (entry, mid, senior) and years required
            4. Education requirements (degree, field)
            5. Key responsibilities
            6. Industry-specific keywords
            7. Soft skills mentioned
            8. Company values/culture mentions
            9. Tools and technologies mentioned
            10. Certifications or qualifications
            11. Exact phrases that should appear in the CV
            
            Format your response as a structured JSON object.
            """
            
            user_prompt = f"""
            Analyze the following job description and extract all key requirements that a candidate should highlight in their CV:
            
            {job_description[:3000]}
            
            Return only a JSON object without any additional text or explanations.
            """
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    job_requirements = json.loads(json_str)
                    return job_requirements
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from job requirement extraction")
                    return {}
            else:
                logger.warning("No JSON found in job requirement extraction response")
                return {}
                
        except Exception as e:
            logger.warning(f"Error in extract_job_requirements: {str(e)}")
            return {}
    
    def process_with_ai(self, job_description, template_data):
        """
        Use AI to enhance CV data based on job description
        
        Args:
            job_description: Job description text
            template_data: Template data to enhance
            
        Returns:
            Enhanced template data
        """
        try:
            import openai
            from app.database import SessionLocal
            from app.models.job import Job
            
            # Get job record from database if available
            job_info = {}
            try:
                db = SessionLocal()
                job_record = db.query(Job).filter(Job.description == job_description).first()
                db.close()
                
                if job_record:
                    job_info = {
                        "id": job_record.id,
                        "title": job_record.title,
                        "company": job_record.company,
                        "location": job_record.location
                    }
                    logger.info(f"Using job record information (ID: {job_record.id}) for CV generation")
            except Exception as e:
                logger.warning(f"Could not load job info from database: {e}")
            
            # Extract job requirements using AI
            job_requirements = self.extract_job_requirements(job_description)
            
            # Set OpenAI API key
            if not self.openai_api_key:
                logger.warning("OpenAI API key not available, skipping AI processing")
                return template_data
                
            openai.api_key = self.openai_api_key
            
            # Define prompts
            system_prompt = """You are a CV generator assistant that creates data structures for multiple CV template formats. Your job is to create a clean, professional CV data structure that will work across different LaTeX CV templates.

IMPORTANT INSTRUCTIONS:
1. Use ONLY the candidate's actual profile data whenever available
2. ONLY supplement with additional information when the candidate profile is clearly missing key information needed for the job
3. NEVER include placeholder text or examples like "Sample Project" or "Short Project Title"
4. NEVER include descriptions with phrases like "quantified success" or "won an award"
5. AVOID using any text that appears to be sample/example content from template sources
6. EXCLUDE any sections that don't have substantial, genuine content - empty or placeholder sections will be excluded
7. For complex sections (like experience, education, skills), ensure each entry has all required fields with actual content
8. NEVER include placeholder content like 'Try it here', 'Sample bullet point', or 'ABC Company'
9. Address data MUST be a simple string, NOT a JSON structure with "line1", "city", etc. fields
10. EXCLUDE any data identified as a placeholder in the user's profile rather than including it

Your job is to clean the data structure for professional presentation across ANY LaTeX CV template."""
            
            # Build a more intelligent prompt that incorporates both the job and candidate profile
            user_prompt = f"""
            Parse this job description and extract key information. IMPORTANT: Tailor the template data to the candidate's existing profile while ensuring relevance to the job description.
            
            JOB DESCRIPTION:
            {job_description[:2000]}
            
            JOB METADATA:
            {json.dumps(job_info, indent=2) if job_info else "No additional job metadata available."}
            
            JOB REQUIREMENTS (AI EXTRACTED):
            {json.dumps(job_requirements, indent=2) if job_requirements else "No job requirements extracted."}
            
            CANDIDATE PROFILE:
            {json.dumps(template_data, indent=2)}
            
            INSTRUCTIONS:
            1. Analyze the candidate profile for any placeholder or sample text - REMOVE ALL placeholder content
            2. Keep ONLY the candidate's real information (name, contact details, photo, etc.)
            3. If the address is in JSON format with fields like "line1", "city", etc. - REMOVE it completely
            4. Remove any projects with titles like "Short Project Title" or "Hiring Search Tool" - these are placeholders
            5. Remove any content containing "Example", "Sample", "Build a project", etc.
            6. Keep only GENUINE skills, experience, education, and certifications from the candidate
            7. For skills field, verify each has a real "name" property that's not a placeholder
            8. Only include fields that have ACTUAL content - if a section would be empty or have only placeholders, exclude it entirely
            9. EXCLUDE the entire section if it only contains sample/placeholder entries
            10. ENSURE every field has an appropriate data type (string, array, etc.)
            11. HIGHLIGHT and PRIORITIZE skills and experiences that match the job requirements
            12. For the profile_summary field, ensure it's tailored to the specific job
            
            Your goal is to produce only a CLEAN, PROFESSIONAL data structure with real content, removing all placeholders.
            The output should fit this structure:
            {{
                "profile_summary": "string",  // Optional - only include if real content exists
                "skills": [  // Optional - only include if real content exists
                    {{"name": "skill name", "level": "Proficient", "category": "category"}}
                ],
                "experience": [  // Optional - only include if real content exists
                    {{
                        "title": "job title",
                        "company": "company name",
                        "location": "location",  // Optional
                        "start_date": "Jan 2020",  // Optional
                        "end_date": "Present",  // Optional
                        "description": "key responsibilities and achievements"  // Optional
                    }}
                ],
                "education": [  // Optional - only include if real content exists
                    {{
                        "degree": "degree name",
                        "institution": "university name",
                        "location": "location",  // Optional
                        "start_date": "2015",  // Optional
                        "end_date": "2019",  // Optional
                        "description": "relevant coursework or achievements"  // Optional
                    }}
                ],
                "certifications": [  // Optional - only include if real content exists
                    {{"name": "certification name", "issuer": "issuing organization", "date": "2021"}}
                ],
                "languages": [  // Optional - only include if real content exists
                    {{"name": "language name", "level": "fluency level"}}
                ],
                "projects": [  // Optional - only include if real content exists
                    {{"name": "project name", "description": "project description"}}
                ]
            }}
            
            Return ONLY the cleaned JSON structure with no additional text or explanation.
            """
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            generated_content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    cv_data = json.loads(json_str)
                    
                    # Process the AI-generated data
                    for key, value in cv_data.items():
                        # For string values, check if they are not empty and not placeholders
                        if isinstance(value, str):
                            if value.strip() and self.is_not_placeholder(value):
                                template_data[key] = value
                        # For lists, only include non-empty lists with valid items
                        elif isinstance(value, list) and value:
                            self.update_template_section(template_data, key, value)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from AI response")
                except Exception as e:
                    logger.warning(f"Error processing AI-generated CV data: {str(e)}")
            else:
                logger.warning("No JSON found in AI response")
        
        except Exception as e:
            logger.warning(f"Error in process_with_ai: {str(e)}")
            
        return template_data
    
    def update_template_section(self, template_data, key, value):
        """
        Update a section of the template data with AI-processed data
        
        Args:
            template_data: Current template data
            key: Section key to update
            value: New value for the section
            
        Returns:
            None (updates template_data in-place)
        """
        # Process different section types
        if key == 'experience':
            filtered_items = [
                exp for exp in value 
                if exp.get('title') and exp.get('company') and
                self.is_not_placeholder(exp.get('title')) and 
                self.is_not_placeholder(exp.get('company'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
        elif key == 'education':
            filtered_items = [
                edu for edu in value
                if edu.get('degree') and edu.get('institution') and
                self.is_not_placeholder(edu.get('degree')) and 
                self.is_not_placeholder(edu.get('institution'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
        elif key == 'skills':
            filtered_items = [
                skill for skill in value
                if skill.get('name') and self.is_not_placeholder(skill.get('name'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
        elif key == 'languages':
            filtered_items = [
                lang for lang in value
                if lang.get('name') and lang.get('level') and
                self.is_not_placeholder(lang.get('name')) and 
                self.is_not_placeholder(lang.get('level'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
        elif key == 'certifications':
            filtered_items = [
                cert for cert in value
                if cert.get('name') and self.is_not_placeholder(cert.get('name'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
        elif key == 'projects':
            filtered_items = [
                proj for proj in value
                if proj.get('name') and self.is_not_placeholder(proj.get('name')) and
                proj.get('description') and self.is_not_placeholder(proj.get('description'))
            ]
            if filtered_items:
                template_data[key] = filtered_items
    
    def is_not_placeholder(self, text):
        """
        Check if text content is not a placeholder
        
        Args:
            text: Text to check
            
        Returns:
            Boolean indicating if the text is not a placeholder
        """
        if not text:
            return False
        if not isinstance(text, str):
            return True
        text_lower = text.lower()
        
        # Common placeholder patterns for various templates
        placeholder_keywords = [
            # General placeholders
            "example", "sample", "placeholder", "not provided", "your", 
            # Template-specific placeholders
            "short project title", "build a project", "try it here", 
            "quantified success", "quanti ed success",
            "spans two lines", "won an award", "a, b, and c",
            "hiring search tool", "over 25000 people", 
            "5000+ queries", "saved and shared", "recruiters",
            "bullet point", "social media posts", "tiktok", "instagram",
            "dream job", "best practices", "20k+ job seekers",
            # Company placeholders
            "abc company", "abc tech", "xyz", "company name", 
            # Academic placeholders
            "no title", "no company", "no name", "no institution", 
            "no degree", "university name", "institution name",
            # Empty or invalid content indicators
            "lorem ipsum"
        ]
        
        # Check for common patterns by keyword
        for keyword in placeholder_keywords:
            if keyword in text_lower:
                return False
        
        # Check for JSON fragments or very short text
        if text.startswith("{") or len(text.strip()) < 2:
            return False
        
        # Check for LinkedIn's default format or other structured placeholders
        if bool(re.search(r'\(\d{4}\s*-\s*(present|current|now)\)', text_lower)) and len(text_lower) < 50:
            return False
        
        # Additional pattern checks for template-specific placeholders
        placeholder_patterns = [
            r'(try|click) (it|here)',
            r'[a-z], [a-z], and [a-z]',
            r'(view(ed)?|reach(ed)?) by \d+k\+',
            r'built (a|an) (tool|app|website)',
            r'(no|not) (provided|specified|listed)',
            r'(this|your) (item|entry)',
            r'default (text|content)',
            r'#\d+'  # Template numbering
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # If it passed all checks, it's likely real content
        return True