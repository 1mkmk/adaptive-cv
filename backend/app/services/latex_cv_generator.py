"""
LaTeX CV Generator - Main module.

This is a compatibility module that provides backward compatibility with the original 
implementation, forwarding calls to the new modular implementation in the latex_cv package.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.services.latex_cv.generator import LaTeXCVGenerator

logger = logging.getLogger(__name__)

def generate_cv_with_template(template_name: str, job_description: str, user_id: Optional[str] = None, format: str = "pdf") -> Dict[str, Any]:
    """
    Generate a CV using a template and job description.
    
    Args:
        template_name: Name of the template to use
        job_description: Job description to use for CV generation
        user_id: Optional user ID
        format: Output format ("pdf" or "latex")
        
    Returns:
        Dictionary with generated CV information
    """
    try:
        # Create LaTeXCVGenerator instance from the new implementation
        generator = LaTeXCVGenerator()
        
        # Call the generate_with_template method
        result = generator.generate_with_template(
            template_name=template_name,
            job_description=job_description,
            user_id=user_id,
            format=format
        )
        
        return result
    except Exception as e:
        logger.error(f"Error generating CV with template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")