import os
import shutil
import subprocess
import logging
import re
import time
import uuid
import base64
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

# Import the modular implementation
from app.services.latex_cv import (
    LaTeXCVGenerator,
    LaTeXCompiler,
    LaTeXDocumentBuilder,
    TemplateAnalyzer,
    get_available_templates,
    normalize_template_id,
    BASE_DIR,
    ASSETS_DIR,
    TEMPLATE_DIR,
    LATEX_OUTPUT_DIR,
    PDF_OUTPUT_DIR,
    TEMPLATES_EXTRACTED_DIR,
    TEMPLATES_ZIPPED_DIR
)

logger = logging.getLogger(__name__)

# Maintain backward compatibility by re-exporting the get_available_templates function
get_templates = get_available_templates

# Create a singleton generator instance for efficient reuse
_latex_generator = None

def get_latex_generator():
    """Get or create the LaTeX CV Generator instance"""
    global _latex_generator
    if _latex_generator is None:
        _latex_generator = LaTeXCVGenerator(
            template_dir=TEMPLATE_DIR,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    return _latex_generator

def generate_cv_from_template(template_name, job_title, company_name, template_data, output_id, job_description=None):
    """
    Generate CV from template using LaTeX - Simplified wrapper for backward compatibility
    
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
    generator = get_latex_generator()
    return generator.generate_cv(
        template_name=template_name,
        job_title=job_title,
        company_name=company_name,
        template_data=template_data,
        output_id=output_id,
        job_description=job_description
    )

def generate_with_template(template_name, job_description, user_id=None, format="pdf"):
    """
    Generate a CV using a template and job description - Wrapper for backward compatibility
    
    Args:
        template_name: Name of the template to use
        job_description: Job description to use for CV generation
        user_id: Optional user ID to fetch profile
        format: Output format ("pdf" or "latex")
        
    Returns:
        Dictionary with generated CV information
    """
    generator = get_latex_generator()
    return generator.generate_with_template(
        template_name=template_name,
        job_description=job_description,
        user_id=user_id,
        format=format
    )