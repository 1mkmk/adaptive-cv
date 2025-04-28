"""
Utility functions for directory handling in the template analyzer.

This module provides functions for ensuring correct file paths and directory structures.
"""

import os
import logging
import datetime
from pathlib import Path

# Import the configuration settings
from backend.app.services.latex_cv.config import ASSETS_DIR, LATEX_OUTPUT_DIR

logger = logging.getLogger(__name__)

def get_correct_output_dir(output_dir=None):
    """
    Get the correct output directory for JSON files.
    This function ensures JSON files are created in the generated directory, never in templates.
    
    Args:
        output_dir: Optional output directory that was passed to the function
        
    Returns:
        Correct output directory path
    """
    # Convert output_dir to Path object if provided
    output_path = Path(output_dir) if output_dir else None
    
    # If we already have an output_dir that is within a 'generated' folder, use it
    if output_path and ('generated' in str(output_path)):
        logger.info(f"Using provided output directory in generated folder: {output_path}")
        return str(output_path)
    
    # Use the configured LATEX_OUTPUT_DIR from config.py
    generated_dir = LATEX_OUTPUT_DIR
    
    # Ensure the directory exists
    os.makedirs(generated_dir, exist_ok=True)
    
    # Look for job directories that follow our pattern (name_company_date_id)
    job_dirs = []
    for item in os.listdir(generated_dir):
        full_path = generated_dir / item
        if full_path.is_dir() and '_' in item:
            job_dirs.append(full_path)
    
    # If we found job directories, use the most recent one
    if job_dirs:
        # Sort by creation time (newest first)
        job_dirs.sort(key=lambda p: os.path.getctime(p), reverse=True)
        return str(job_dirs[0])
    
    # If no job directories found, create a temporary one
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_dir = generated_dir / f"temp_json_dir_{timestamp}"
    os.makedirs(temp_dir, exist_ok=True)
    return str(temp_dir)