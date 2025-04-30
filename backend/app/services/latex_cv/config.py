"""
Configuration settings for LaTeX CV generation.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Get base directory from environment variable or default to current path
def get_base_dir():
    env_base_dir = os.environ.get('ADAPTIVE_CV_BASE_DIR')
    if env_base_dir:
        base_dir = Path(env_base_dir)
        logger.info(f"Using base directory from environment: {base_dir}")
    else:
        base_dir = Path(__file__).parent.parent.parent.parent.parent  # Path to project root
        logger.info(f"Using derived base directory: {base_dir}")
    
    if not base_dir.exists():
        logger.warning(f"Base directory does not exist: {base_dir}")
    
    return base_dir

# Base paths
BASE_DIR = get_base_dir()
ASSETS_DIR = BASE_DIR / "assets"

# Directory for LaTeX templates
TEMPLATE_DIR = ASSETS_DIR / "templates"

# Directory for LaTeX output (temporary .tex files)
LATEX_OUTPUT_DIR = ASSETS_DIR / "generated" / "latex"

# Directory for PDF output (final PDF files)
PDF_OUTPUT_DIR = ASSETS_DIR / "generated" / "pdf"

# Directory for extracted templates
TEMPLATES_EXTRACTED_DIR = TEMPLATE_DIR / "templates_extracted"
TEMPLATES_ZIPPED_DIR = TEMPLATE_DIR / "templates_zipped"

# Create directories if they don't exist
for directory in [TEMPLATE_DIR, LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR, 
                 TEMPLATES_EXTRACTED_DIR, TEMPLATES_ZIPPED_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except PermissionError:
        logger.error(f"Permission denied when creating directory: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")

# Make sure PDF_OUTPUT_DIR is not nested within LATEX_OUTPUT_DIR or vice versa
if str(PDF_OUTPUT_DIR).startswith(str(LATEX_OUTPUT_DIR)) or str(LATEX_OUTPUT_DIR).startswith(str(PDF_OUTPUT_DIR)):
    logger.warning("PDF and LaTeX output directories should not be nested within each other!")

# Share relevant directories as constants for application use
DEFAULT_PHOTO_DIR = ASSETS_DIR / "photos"
if not DEFAULT_PHOTO_DIR.exists():
    try:
        os.makedirs(DEFAULT_PHOTO_DIR, exist_ok=True)
        logger.debug(f"Created default photo directory: {DEFAULT_PHOTO_DIR}")
    except Exception as e:
        logger.error(f"Error creating photo directory: {str(e)}")

# Maximum allowed file sizes (in bytes)
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_TEMPLATE_SIZE = 20 * 1024 * 1024  # 20 MB

# Allowed file extensions
ALLOWED_PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_TEMPLATE_EXTENSIONS = ['.zip']