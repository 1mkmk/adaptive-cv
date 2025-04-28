"""
JSON handling utilities for template analyzer.

This module provides functions for creating and manipulating JSON files used in template analysis.
"""

import os
import json
import copy
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from backend.app.services.latex_cv.config import LATEX_OUTPUT_DIR
from .directory_utils import get_correct_output_dir

logger = logging.getLogger(__name__)

def get_job_output_dir(job_id: Optional[str] = None, output_dir: Optional[str] = None) -> str:
    """
    Get or create job-specific output directory in the generated folder.
    
    Args:
        job_id: Unique identifier for the job
        output_dir: Optional output directory provided by the caller
        
    Returns:
        Path to job-specific output directory
    """
    # If no job_id provided, use timestamp as fallback
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"job_{job_id}" if job_id else f"job_{timestamp}"
    
    # If output_dir was provided and contains the job_id, use it
    if output_dir and job_id and job_id in str(output_dir):
        job_dir = Path(output_dir)
    else:
        # Create new directory in the generated latex folder
        job_dir = Path(LATEX_OUTPUT_DIR) / folder_name
        
    # Ensure directory exists
    os.makedirs(job_dir, exist_ok=True)
    logger.info(f"Using job directory: {job_dir}")
    
    return str(job_dir)

def create_profile_json(output_dir: str, template_data: Dict[str, Any], job_id: Optional[str] = None) -> str:
    """
    Create a profile.json file in the output directory.
    
    Args:
        output_dir: Directory where the file should be created
        template_data: User profile data
        job_id: Unique identifier for the job
        
    Returns:
        Path to created profile.json file
    """
    try:
        # Get job-specific output directory
        job_dir = get_job_output_dir(job_id, output_dir)
        profile_path = Path(job_dir) / 'profile.json'
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            profile_data = {
                "profile_data": template_data,
                "creation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile_summary": "Profile data extracted from user database"
            }
            json.dump(profile_data, f, indent=2)
            logger.info(f"Created profile.json at {profile_path}")
            
        return str(profile_path)
    except Exception as e:
        logger.warning(f"Error creating profile.json: {str(e)}")
        return ""

def create_job_requirements_json(output_dir: str, ai_analysis: Dict[str, Any], job_id: Optional[str] = None) -> str:
    """
    Create a job_requirements.json file from the AI analysis.
    
    Args:
        output_dir: Directory where the file should be created
        ai_analysis: AI-generated analysis including job requirements
        job_id: Unique identifier for the job
        
    Returns:
        Path to created job_requirements.json file or empty string on failure
    """
    try:
        # Only proceed if we have the required data
        if "job_match" not in ai_analysis or "extracted_requirements" not in ai_analysis["job_match"]:
            logger.warning("No job requirements found in AI analysis")
            return ""
            
        # Get job-specific output directory
        job_dir = get_job_output_dir(job_id, output_dir)
        job_req_path = Path(job_dir) / 'job_requirements.json'
        
        with open(job_req_path, 'w', encoding='utf-8') as f:
            job_req_data = {
                "job_requirements": ai_analysis["job_match"]["extracted_requirements"],
                "creation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "extracted_from": "Job description analysis via OpenAI"
            }
            json.dump(job_req_data, f, indent=2)
            logger.info(f"Created job_requirements.json at {job_req_path}")
            
        return str(job_req_path)
    except Exception as e:
        logger.warning(f"Error creating job_requirements.json: {str(e)}")
        return ""

def create_merged_json(output_dir: str, profile_data: Dict[str, Any], 
                     ai_analysis: Dict[str, Any], job_id: Optional[str] = None) -> str:
    """
    Create a merged JSON file that combines profile data, job requirements, and template analysis
    
    Args:
        output_dir: Directory where the merged.json file should be created
        profile_data: User profile data
        ai_analysis: AI-generated analysis including job requirements and template analysis
        job_id: Unique identifier for the job
        
    Returns:
        Path to created merged.json file or empty string on failure
    """
    try:
        # Get job-specific output directory
        job_dir = get_job_output_dir(job_id, output_dir)
        merged_path = Path(job_dir) / 'merged.json'
        
        # Extract job requirements if available
        job_requirements = {}
        if "job_match" in ai_analysis and "extracted_requirements" in ai_analysis["job_match"]:
            job_requirements = ai_analysis["job_match"]["extracted_requirements"]
        
        # Extract template recommendations if available
        template_recommendations = {}
        if "template_specific_recommendations" in ai_analysis:
            template_recommendations = ai_analysis["template_specific_recommendations"]
        elif "job_match" in ai_analysis and "template_specific_recommendations" in ai_analysis["job_match"]:
            template_recommendations = ai_analysis["job_match"]["template_specific_recommendations"]
            
        # Extract profile enhancement suggestions if available
        profile_enhancement = {}
        if "job_match" in ai_analysis and "profile_enhancement" in ai_analysis["job_match"]:
            profile_enhancement = ai_analysis["job_match"]["profile_enhancement"]
            
        # Create enhanced profile by merging original profile with AI insights
        enhanced_profile = copy.deepcopy(profile_data)
        
        # Add AI-generated improvements to the profile
        if profile_enhancement:
            if "matches" in profile_enhancement:
                enhanced_profile["strengths"] = profile_enhancement["matches"]
            if "gaps" in profile_enhancement:
                enhanced_profile["areas_for_improvement"] = profile_enhancement["gaps"]
            if "improvement_suggestions" in profile_enhancement:
                enhanced_profile["improvement_suggestions"] = profile_enhancement["improvement_suggestions"]
        
        # Build the merged data structure
        merged_data = {
            "profile": enhanced_profile,
            "job_requirements": job_requirements,
            "template_recommendations": template_recommendations,
            "optimization_suggestions": ai_analysis.get("optimization_suggestions", {}),
            "metadata": {
                "creation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "generated_by": "AdaptiveCV Template Analyzer",
                "job_id": job_id if job_id else "unspecified"
            }
        }
        
        # Write merged data to file
        with open(merged_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2)
            
        logger.info(f"Created merged.json at {merged_path}")
        return str(merged_path)
        
    except Exception as e:
        logger.error(f"Error creating merged.json: {str(e)}")
        return ""

def save_template_json(output_dir: str, ai_analysis: Dict[str, Any], job_id: Optional[str] = None) -> str:
    """
    Save the AI analysis to template.json
    
    Args:
        output_dir: Directory where the file should be created
        ai_analysis: AI-generated template analysis
        job_id: Unique identifier for the job
        
    Returns:
        Path to created template.json file or empty string on failure
    """
    try:
        # Get job-specific output directory
        job_dir = get_job_output_dir(job_id, output_dir)
        template_path = Path(job_dir) / 'template.json'
        
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(ai_analysis, f, indent=2)
            logger.info(f"Created template.json at {template_path}")
            
        return str(template_path)
    except Exception as e:
        logger.warning(f"Error creating template.json: {str(e)}")
        return ""