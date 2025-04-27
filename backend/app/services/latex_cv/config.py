"""
Configuration settings for LaTeX CV generation.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent  # Path to project root
ASSETS_DIR = BASE_DIR / "assets"

# Directory for LaTeX templates
TEMPLATE_DIR = ASSETS_DIR / "templates"

# Directory for LaTeX output (temporary .tex files)
LATEX_OUTPUT_DIR = ASSETS_DIR / "generated" / "latex"

# Directory for PDF output (final PDF files)
PDF_OUTPUT_DIR = ASSETS_DIR / "generated" / "pdf"

# Directory for extracted templates
TEMPLATES_EXTRACTED_DIR = ASSETS_DIR / "templates" / "templates_extracted"
TEMPLATES_ZIPPED_DIR = ASSETS_DIR / "templates" / "templates_zipped"

# Create directories if they don't exist
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_EXTRACTED_DIR, exist_ok=True)