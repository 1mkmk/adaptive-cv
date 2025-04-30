"""
OpenAI-based template analysis functions.

This module contains functions for analyzing templates using OpenAI to generate
comprehensive analysis data.
"""

import os
import re
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_ai_template_analysis(template_info: Dict[str, Any], 
                               job_description: str, template_data: Dict[str, Any], 
                               template_name: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive template analysis using OpenAI
    
    Args:
        template_info: Basic template structure information
        job_description: Job description text
        template_data: Candidate profile data
        template_name: Template name
        output_dir: Output directory (latex_output_dir) where files should be saved
        
    Returns:
        Dictionary with comprehensive template analysis and job matching
    """
    try:
        import openai
    except ImportError:
        logger.warning("OpenAI package not installed, skipping AI template analysis")
        return {}
    
    # Set OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OpenAI API key not available, skipping AI template analysis")
        return {}
        
    openai.api_key = openai_api_key
    
    # Use the latex_output_dir provided by the generator
    latex_output_dir = output_dir
    
    if not latex_output_dir or not os.path.exists(latex_output_dir):
        logger.warning(f"Output directory does not exist: {latex_output_dir}")
        return {}
        
    logger.info(f"Using latex_output_dir for storing JSON files: {latex_output_dir}")
    
    # Define prompts for creating the analysis
    system_prompt = """You are an AI assistant specialized in analyzing LaTeX templates, job descriptions, and candidate profiles for CV generation. 
    Your task is to analyze a LaTeX template, a job description, and a candidate profile, producing a comprehensive analysis that contains:
    
    1. Complete template analysis including all available fields, structure, customization options, and LaTeX commands
    2. Detailed job requirements extracted from the job description
    3. Analysis of how well the candidate's profile matches the job requirements
    4. Identification of the candidate's strengths and weaknesses relative to the job
    5. Suggestions for improving the profile to better match the job
    6. Template-specific recommendations for highlighting key qualifications
    
    Your output should be a single, well-structured JSON object with all this information.
    """
    
    user_prompt = f"""
    Create a comprehensive analysis for a CV generation system with the following inputs:
    
    TEMPLATE INFO:
    {json.dumps(template_info, indent=2)}
    
    JOB DESCRIPTION:
    {job_description[:2000] if job_description else "No job description provided."}
    
    CANDIDATE PROFILE DATA:
    {json.dumps(template_data, indent=2)}
    
    TEMPLATE NAME: {template_name}
    
    FORMAT YOUR RESPONSE AS A SINGLE, WELL-STRUCTURED JSON OBJECT with these main sections:
    1. "strengths": Strengths of this template
    2. "weaknesses": Weaknesses or limitations of this template
    3. "optimal_uses": When this template is best used
    4. "customization_options": Key ways this template can be customized
    5. "section_mapping": How template sections map to candidate data fields
    6. "job_match": Comprehensive analysis of how the candidate profile matches the job requirements, including:
       - extracted_requirements (detailed breakdown of job requirements including required and preferred skills, years of experience, education, etc.)
       - profile_enhancement (analysis of matches, gaps, and improvement suggestions)
       - template_specific_recommendations (how to use this specific template to highlight key qualifications)
    7. "document_structure": Analysis of the LaTeX document's structure
    8. "optimization_suggestions": Specific suggestions for optimizing the CV for this job posting
    
    IMPORTANT: Do NOT wrap your response in a "template_analysis" key. The entire response should be a flat JSON object with the above keys at the root level.
    
    Return ONLY a valid JSON object without any additional text or explanation.
    """
    
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        generated_content = response.choices[0].message.content.strip()
        
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                ai_analysis = json.loads(json_str)
                
                # Save the detailed analysis to template.json in the latex_output_dir
                # Store the analysis directly without the template_analysis wrapper
                template_json_path = os.path.join(latex_output_dir, 'template.json')
                with open(template_json_path, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2)
                logger.info(f"Saved template analysis to {template_json_path}")
                
                # Create job_requirements.json from the AI analysis in the latex_output_dir
                job_requirements = {}
                if "job_match" in ai_analysis and "extracted_requirements" in ai_analysis["job_match"]:
                    job_requirements = ai_analysis["job_match"]["extracted_requirements"]
                
                job_req_path = os.path.join(latex_output_dir, 'job_requirements.json')
                with open(job_req_path, 'w', encoding='utf-8') as f:
                    json.dump(job_requirements, f, indent=2)
                logger.info(f"Saved job requirements to {job_req_path}")
                
                # Save the profile as a separate JSON file
                profile_path = os.path.join(latex_output_dir, 'profile.json')
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)
                logger.info(f"Saved profile data to {profile_path}")
                
                # Create merged.json combining profile, job requirements and template analysis
                # Store the template analysis directly without the template_analysis wrapper
                merged_data = {
                    "profile": template_data,
                    "job_requirements": job_requirements,
                    "template": ai_analysis  # Changed from "template_analysis": ai_analysis
                }
                
                merged_path = os.path.join(latex_output_dir, 'merged.json')
                with open(merged_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, indent=2)
                logger.info(f"Saved merged analysis to {merged_path}")
                
                return ai_analysis
            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON from AI template analysis response")
                return {}
        else:
            logger.warning("No JSON found in AI template analysis response")
            return {}
            
    except Exception as e:
        logger.warning(f"Error generating AI template analysis: {str(e)}")
        return {}