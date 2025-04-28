"""
AI-assisted template filling functions.

This module contains functions for filling LaTeX templates with real data using
OpenAI's language models to intelligently adapt content.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List

from .directory_utils import get_correct_output_dir

logger = logging.getLogger(__name__)

def ai_fill_template(template_dir: str, output_dir: str, template_data: Dict[str, Any], 
                    template_info: Dict[str, Any], job_description: str) -> List[str]:
    """
    Use OpenAI to fill the entire template based on comprehensive analysis
    
    Args:
        template_dir: Path to source template directory
        output_dir: Path to output directory
        template_data: User data to fill the template with
        template_info: Template analysis information including AI analysis
        job_description: Job description text
        
    Returns:
        List of modified files
    """
    try:
        import openai
    except ImportError:
        logger.warning("OpenAI package not installed, skipping AI template filling")
        return []
    
    modified_files = []
    
    # Set OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OpenAI API key not available, skipping AI template filling")
        return modified_files
        
    openai.api_key = openai_api_key
    
    # Ensure we're using the correct output directory
    correct_output_dir = get_correct_output_dir(output_dir)
    if correct_output_dir != output_dir:
        logger.info(f"Redirecting AI template filling from {output_dir} to {correct_output_dir}")
        output_dir = correct_output_dir
    
    # Read all main template files
    template_files_content = {}
    for rel_path in template_info.get("main_files", []):
        file_path = os.path.join(template_dir, rel_path)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                template_files_content[rel_path] = f.read()
        except Exception as e:
            logger.warning(f"Error reading template file {file_path}: {str(e)}")
    
    if not template_files_content:
        logger.warning("No template files found for AI filling")
        return modified_files
    
    # Define prompts for AI filling
    system_prompt = """You are an AI assistant specialized in generating LaTeX CV documents. Your task is to fill a LaTeX template with candidate data, optimizing it for a specific job description. 
    
    Follow these rules:
    1. Maintain the overall LaTeX structure and commands of the original template
    2. Replace placeholder content with real candidate data
    3. Ensure proper LaTeX syntax including escaping special characters
    4. Highlight skills and experiences that match the job requirements
    5. Format content professionally and consistently
    6. Only modify the actual content, not the template structure itself
    
    Your output should be valid LaTeX files that will compile without errors.
    """
    
    # Process each main file
    for rel_path, template_content in template_files_content.items():
        output_path = os.path.join(output_dir, rel_path)
        
        # Create the prompt for this specific file
        user_prompt = f"""
        Fill the following LaTeX template with the candidate's data, optimized for the job description.
        
        JOB DESCRIPTION:
        {job_description[:1500] if job_description else "No job description provided."}
        
        CANDIDATE PROFILE DATA:
        {json.dumps(template_data, indent=2)}
        
        TEMPLATE ANALYSIS:
        {json.dumps(template_info.get("template_analysis", {}), indent=2)}
        {json.dumps(template_info.get("section_mapping", {}), indent=2)}
        
        ORIGINAL TEMPLATE CONTENT:
        ```latex
        {template_content}
        ```
        
        INSTRUCTIONS:
        1. Fill in the template with the candidate's data
        2. Highlight skills and experiences relevant to the job
        3. Maintain correct LaTeX syntax
        4. Ensure special characters are properly escaped
        5. Remove any placeholder content or sample data
        6. Format the content professionally
        
        Return ONLY the filled LaTeX content without any additional explanations or markdown formatting. Just the plain LaTeX content that I can directly write to a file.
        """
        
        try:
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
            
            filled_content = response.choices[0].message.content.strip()
            
            # Remove any markdown code block markers if present
            filled_content = re.sub(r'^```latex\s*', '', filled_content)
            filled_content = re.sub(r'\s*```$', '', filled_content)
            
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the filled content to the output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(filled_content)
            
            logger.info(f"AI filled template file: {output_path}")
            modified_files.append(rel_path)
            
        except Exception as e:
            logger.error(f"Error in AI template filling for {rel_path}: {str(e)}")
    
    return modified_files