"""
AI-powered profile generation services.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configure OpenAI - try to import but don't fail if not available
try:
    import openai
except ImportError:
    logger.warning("OpenAI module not installed. AI-based generation will not be available.")
    openai = None

class ProfileAIGenerator:
    """
    Class for generating profile data using OpenAI
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the profile AI generator
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Validate API key format
        if self.api_key and len(self.api_key) > 20:
            if openai:
                openai.api_key = self.api_key
                logger.info(f"OpenAI API key configured (starting with: {self.api_key[:4]}...)")
            else:
                logger.warning("OpenAI API key configured but OpenAI module is not available")
        else:
            logger.warning("No valid OpenAI API key provided")
            self.api_key = None
            
    async def generate_profile_from_prompt(self, prompt: str, creativity_levels: Dict[str, int] = None, 
                                     job_description: str = None) -> Dict[str, Any]:
        """
        Generate a profile based on a prompt and creativity levels
        
        Args:
            prompt: Text prompt describing the profile to generate
            creativity_levels: Dictionary mapping profile sections to creativity levels (0-10)
            job_description: Optional job description to tailor the profile to
            
        Returns:
            Dictionary with generated profile data
        """
        if not openai or not self.api_key:
            raise ValueError("OpenAI API not available or not configured")
        
        # Use default creativity levels if not provided
        if creativity_levels is None:
            creativity_levels = {
                "summary": 5,
                "experience": 5,
                "education": 3,
                "skills": 4,
                "projects": 6
            }
        
        # Include creativity levels and job description in the prompt
        creativity_desc = "\n".join([f"- {section}: {level}/10 creativity level" for section, level in creativity_levels.items()])
        
        job_desc_text = ""
        if job_description:
            job_desc_text = f"\nPlease tailor the profile to this job description:\n{job_description}"
        
        # Prepare comprehensive prompt for profile generation
        prompt_template = f"""
        Generate a complete CV profile based on this prompt:
        
        "{prompt}"
        
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
        
        # Determine OpenAI API version and make the API call
        try:
            if hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                logger.info("Using OpenAI API v1.0+ (Client)")
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer who creates complete, realistic CV profiles based on user prompts."},
                        {"role": "user", "content": prompt_template}
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
                        {"role": "user", "content": prompt_template}
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
                
                return profile_data
                
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse OpenAI response as JSON: {json_err}")
                logger.error(f"Response: {result}")
                raise ValueError("Failed to parse generated profile. Please try again.")
                
        except Exception as openai_err:
            logger.error(f"Error using OpenAI: {openai_err}")
            raise ValueError(f"Failed to generate profile: {str(openai_err)}")

    @staticmethod
    def check_openai_availability() -> Dict[str, Any]:
        """
        Check if OpenAI API is available and configured
        
        Returns:
            Dictionary with availability status
        """
        api_key = os.getenv("OPENAI_API_KEY", "")
        has_valid_key = api_key is not None and len(api_key) > 20
        openai_module_available = openai is not None
        
        return {
            "has_valid_key": has_valid_key,
            "key_status": "configured" if has_valid_key else "not_configured",
            "openai_module_available": openai_module_available,
            "message": "OpenAI API key configured and ready to use" if (has_valid_key and openai_module_available) else 
                       "OpenAI module not installed" if not openai_module_available else
                       "Please set the OPENAI_API_KEY environment variable to use OpenAI features"
        }